import json
from datetime import date
from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from sgr_app.models import (
    Usuario, Delegacion, Cargo, PeriodoMedicion, CatalogoServicio,
    ItemMedicion, CompromisoAgenda, Actividad, Evidencia,
    CasoSocial, AtencionSocial, RegistroAuditoria
)
from sgr_app.serializers import (
    UsuarioSerializer, DelegacionSerializer, CargoSerializer,
    PeriodoMedicionSerializer, CatalogoServicioSerializer,
    ItemMedicionSerializer, CompromisoAgendaSerializer,
    ActividadSerializer, EvidenciaSerializer,
    CasoSocialSerializer, AtencionSocialSerializer,
    RegistroAuditoriaSerializer
)
from sgr_app.services.calculos import (
    calcular_metricas_funcionario,
    calcular_resumen_delegacion,
    calcular_resumen_comunal
)


def registrar_evento_auditoria(request, usuario, accion, entidad, identificador, val_ant=None, val_nuevo=None):
    try:
        ip = request.META.get('REMOTE_ADDR') if request else '127.0.0.1'
        RegistroAuditoria.objects.create(
            usuario=usuario,
            accion=accion,
            entidad=entidad,
            identificador_registro=str(identificador),
            valor_anterior=val_ant,
            valor_nuevo=val_nuevo,
            ip_origen=ip
        )
    except Exception as e:
        print(f"Error registrando auditoría: {e}")


class AuthLoginView(APIView):
    """
    Login seguro con autenticación de credenciales y preparación para 2FA.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Debe proporcionar usuario y contraseña.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {'error': 'Credenciales inválidas o usuario inactivo.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Si el usuario tiene 2FA activado (módulo de Rodrigo)
        if user.requires_2fa and not user.is_2fa_verified:
            return Response({
                'requires_2fa': True,
                'user_id': user.id,
                'username': user.username,
                'message': 'Autenticación en dos pasos requerida.'
            }, status=status.HTTP_200_OK)

        registrar_evento_auditoria(request, user, 'INICIO_SESION', 'Usuario', user.id, None, {'username': user.username})

        serializer = UsuarioSerializer(user)
        return Response({
            'requires_2fa': False,
            'user': serializer.data,
            'token': f"sgr-token-{user.id}-{timezone.now().timestamp()}"
        }, status=status.HTTP_200_OK)


class Verificar2FAView(APIView):
    """
    Endpoint preparado para que Rodrigo valide el código TOTP / 2FA.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        code = request.data.get('code')

        try:
            user = Usuario.objects.get(id=user_id)
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # En ambiente académico / prototipo, el código de prueba estándar es '123456' o cualquier código numérico de 6 dígitos
        if code and len(code) == 6:
            user.is_2fa_verified = True
            user.save()
            registrar_evento_auditoria(request, user, 'VERIFICACION_2FA', 'Usuario', user.id)
            serializer = UsuarioSerializer(user)
            return Response({
                'success': True,
                'user': serializer.data,
                'token': f"sgr-token-{user.id}-{timezone.now().timestamp()}"
            })
        else:
            return Response({'error': 'Código 2FA incorrecto o inválido'}, status=status.HTTP_400_BAD_REQUEST)


class DelegacionViewSet(viewsets.ModelViewSet):
    queryset = Delegacion.objects.all()
    serializer_class = DelegacionSerializer


class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def get_queryset(self):
        qs = Usuario.objects.all()
        delegacion_id = self.request.query_params.get('delegacion')
        rol = self.request.query_params.get('rol')
        if delegacion_id:
            qs = qs.filter(delegacion_id=delegacion_id)
        if rol:
            qs = qs.filter(rol=rol)
        return qs


class PeriodoMedicionViewSet(viewsets.ModelViewSet):
    queryset = PeriodoMedicion.objects.all()
    serializer_class = PeriodoMedicionSerializer


class CatalogoServicioViewSet(viewsets.ModelViewSet):
    queryset = CatalogoServicio.objects.filter(activo=True)
    serializer_class = CatalogoServicioSerializer


class ItemMedicionViewSet(viewsets.ModelViewSet):
    queryset = ItemMedicion.objects.all()
    serializer_class = ItemMedicionSerializer

    def get_queryset(self):
        qs = ItemMedicion.objects.all()
        cargo_id = self.request.query_params.get('cargo')
        periodo_id = self.request.query_params.get('periodo')
        if cargo_id:
            qs = qs.filter(cargo_id=cargo_id)
        if periodo_id:
            qs = qs.filter(periodo_id=periodo_id)
        return qs


class CompromisoAgendaViewSet(viewsets.ModelViewSet):
    """
    Tubo de Trabajo / Agenda Colectiva.
    Permite transiciones controladas de estado y auditoría.
    """
    queryset = CompromisoAgenda.objects.all()
    serializer_class = CompromisoAgendaSerializer

    def get_queryset(self):
        qs = CompromisoAgenda.objects.all()
        delegacion_id = self.request.query_params.get('delegacion')
        responsable_id = self.request.query_params.get('responsable')
        estado = self.request.query_params.get('estado')
        if delegacion_id:
            qs = qs.filter(delegacion_id=delegacion_id)
        if responsable_id:
            qs = qs.filter(responsable_id=responsable_id)
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def perform_create(self, serializer):
        compromiso = serializer.save()
        registrar_evento_auditoria(
            self.request,
            self.request.user if self.request.user.is_authenticated else compromiso.responsable,
            'CREAR', 'CompromisoAgenda', compromiso.id, None, {'solicitante': compromiso.solicitante}
        )

    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        compromiso = self.get_object()
        nuevo_estado = request.data.get('estado')
        observacion = request.data.get('observacion', '')

        if nuevo_estado not in CompromisoAgenda.Estado.values:
            return Response({'error': f'Estado inválido: {nuevo_estado}'}, status=status.HTTP_400_BAD_REQUEST)

        antiguo_estado = compromiso.estado
        compromiso.estado = nuevo_estado
        if observacion:
            compromiso.observaciones = f"{compromiso.observaciones or ''}\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] {observacion}".strip()
        compromiso.save()

        registrar_evento_auditoria(
            request,
            request.user if request.user.is_authenticated else compromiso.responsable,
            'CAMBIO_ESTADO', 'CompromisoAgenda', compromiso.id,
            {'estado': antiguo_estado}, {'estado': nuevo_estado, 'observacion': observacion}
        )

        return Response(CompromisoAgendaSerializer(compromiso).data)


class ActividadViewSet(viewsets.ModelViewSet):
    """
    CRUD del registro de actividades diarias de los funcionarios.
    """
    queryset = Actividad.objects.all()
    serializer_class = ActividadSerializer

    def get_queryset(self):
        qs = Actividad.objects.all().select_related('funcionario', 'delegacion', 'item_medicion', 'evidencia')
        delegacion_id = self.request.query_params.get('delegacion')
        funcionario_id = self.request.query_params.get('funcionario')
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')

        if delegacion_id:
            qs = qs.filter(delegacion_id=delegacion_id)
        if funcionario_id:
            qs = qs.filter(funcionario_id=funcionario_id)
        if fecha_desde:
            qs = qs.filter(fecha_actividad__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_actividad__lte=fecha_hasta)
        return qs

    def create(self, request, *args, **kwargs):
        # Permite registrar actividad y evidencia en una sola operación optimizada para móvil (<= 3 clics)
        data = request.data.copy()
        
        # Si el funcionario no viene en data, usar el logueado o fallback
        funcionario_id = data.get('funcionario')
        if not funcionario_id and request.user.is_authenticated:
            data['funcionario'] = request.user.id
            if not data.get('delegacion') and request.user.delegacion:
                data['delegacion'] = request.user.delegacion.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        actividad = serializer.save()

        # Generar evidencia vinculada de inmediato con su código alfanumérico único
        foto_archivo = request.FILES.get('archivo_foto')
        url_simulada = data.get('url_foto_simulada') or ''

        evidencia = Evidencia.objects.create(
            actividad=actividad,
            archivo_foto=foto_archivo,
            url_foto_simulada=url_simulada or 'https://images.unsplash.com/photo-1541888946425-d0fbb1861564?auto=format&fit=crop&w=600&q=80',
            estado=Evidencia.Estado.PENDIENTE
        )

        registrar_evento_auditoria(
            request,
            actividad.funcionario,
            'CREAR', 'Actividad', actividad.id,
            None, {'actividad': actividad.actividad_solicitud, 'codigo_evidencia': evidencia.codigo_verificador}
        )

        headers = self.get_success_headers(serializer.data)
        # Recargar para incluir evidencia
        return Response(ActividadSerializer(actividad).data, status=status.HTTP_201_CREATED, headers=headers)


class EvidenciaViewSet(viewsets.ModelViewSet):
    """
    Gestión de Evidencias y módulo de validación ("Check" del Delegado/Verificador).
    """
    queryset = Evidencia.objects.all().select_related('actividad', 'verificador')
    serializer_class = EvidenciaSerializer

    def get_queryset(self):
        qs = Evidencia.objects.all()
        delegacion_id = self.request.query_params.get('delegacion')
        estado = self.request.query_params.get('estado')
        if delegacion_id:
            qs = qs.filter(actividad__delegacion_id=delegacion_id)
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    @action(detail=True, methods=['post'], url_path='validar')
    def validar(self, request, pk=None):
        """
        Botón de validación del Delegado: Aprobar, Rechazar o Corrección.
        """
        evidencia = self.get_object()
        decision = request.data.get('decision') # APROBADA, RECHAZADA, CORRECCION
        observacion = request.data.get('observacion', '')
        verificador_id = request.data.get('verificador')

        if decision not in Evidencia.Estado.values:
            return Response({'error': f'Decisión no válida: {decision}'}, status=status.HTTP_400_BAD_REQUEST)

        verificador = None
        if verificador_id:
            try:
                verificador = Usuario.objects.get(id=verificador_id)
            except Usuario.DoesNotExist:
                pass
        elif request.user.is_authenticated:
            verificador = request.user

        # RN-009 y CA-07: Segregación de Funciones
        if verificador:
            if verificador.rol == Usuario.Rol.FUNCIONARIO:
                return Response(
                    {'error': 'Segregación de funciones (RN-009): Un funcionario de terreno no puede auto-aprobar o validar evidencias.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if verificador.rol == Usuario.Rol.DELEGADO and verificador.delegacion:
                if evidencia.actividad.delegacion_id != verificador.delegacion_id:
                    return Response(
                        {'error': f'Acceso restringido: Solo puedes validar evidencias de tu propia delegación ({verificador.delegacion.nombre}).'},
                        status=status.HTTP_403_FORBIDDEN
                    )

        antiguo_estado = evidencia.estado
        evidencia.estado = decision
        evidencia.observacion = observacion
        evidencia.verificador = verificador
        evidencia.fecha_validacion = timezone.now()
        evidencia.save()

        registrar_evento_auditoria(
            request,
            verificador,
            'VALIDAR_EVIDENCIA', 'Evidencia', evidencia.id,
            {'estado': antiguo_estado},
            {'estado': decision, 'observacion': observacion, 'codigo': evidencia.codigo_verificador}
        )

        return Response(EvidenciaSerializer(evidencia).data)


class MetricasAPIView(APIView):
    """
    Endpoints analíticos de métricas del semáforo.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        tipo = request.query_params.get('tipo', 'comunal') # comunal, delegacion, funcionario
        periodo_id = request.query_params.get('periodo')
        
        if periodo_id:
            periodo = PeriodoMedicion.objects.filter(id=periodo_id).first()
        else:
            periodo = PeriodoMedicion.objects.filter(cerrado=False).first() or PeriodoMedicion.objects.first()

        if not periodo:
            return Response({'error': 'No hay períodos de medición registrados.'}, status=status.HTTP_404_NOT_FOUND)

        if tipo == 'comunal':
            data = calcular_resumen_comunal(periodo)
            return Response(data)

        elif tipo == 'delegacion':
            delegacion_id = request.query_params.get('delegacion_id')
            if not delegacion_id:
                return Response({'error': 'delegacion_id requerido'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                delegacion = Delegacion.objects.get(id=delegacion_id)
            except Delegacion.DoesNotExist:
                return Response({'error': 'Delegación no encontrada'}, status=status.HTTP_404_NOT_FOUND)
            data = calcular_resumen_delegacion(delegacion, periodo)
            return Response(data)

        elif tipo == 'funcionario':
            funcionario_id = request.query_params.get('funcionario_id')
            if not funcionario_id:
                return Response({'error': 'funcionario_id requerido'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                funcionario = Usuario.objects.get(id=funcionario_id)
            except Usuario.DoesNotExist:
                return Response({'error': 'Funcionario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
            data = calcular_metricas_funcionario(funcionario, periodo)
            return Response(data)

        return Response({'error': 'Tipo no reconocido'}, status=status.HTTP_400_BAD_REQUEST)


class CasoSocialViewSet(viewsets.ModelViewSet):
    queryset = CasoSocial.objects.all().prefetch_related('atenciones')
    serializer_class = CasoSocialSerializer


class AtencionSocialViewSet(viewsets.ModelViewSet):
    queryset = AtencionSocial.objects.all()
    serializer_class = AtencionSocialSerializer


class RegistroAuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RegistroAuditoria.objects.all()
    serializer_class = RegistroAuditoriaSerializer
