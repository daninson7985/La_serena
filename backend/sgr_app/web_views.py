from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from sgr_app.models import (
    Delegacion, Cargo, Usuario, PeriodoMedicion, ItemMedicion,
    Actividad, Evidencia, CompromisoAgenda, CasoSocial, AtencionSocial,
    RegistroAuditoria
)
from sgr_app.services.calculos import (
    calcular_metricas_funcionario,
    calcular_resumen_delegacion,
    calcular_resumen_comunal,
    determinar_color_semaforo
)

def web_login(request):
    if request.user.is_authenticated:
        if request.user.rol == Usuario.Rol.FUNCIONARIO:
            return redirect('web_personal')
        return redirect('web_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        requires_2fa = request.POST.get('requires_2fa') == 'on'

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if requires_2fa or user.requires_2fa:
                return render(request, 'login.html', {
                    'show_2fa': True,
                    'user_id': user.id
                })
            login(request, user)
            RegistroAuditoria.objects.create(
                usuario=user, accion='INICIO_SESION', entidad='Usuario',
                identificador_registro=str(user.id),
                valor_nuevo={'username': user.username},
                ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
            if user.rol == Usuario.Rol.FUNCIONARIO:
                return redirect('web_personal')
            return redirect('web_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Credenciales inválidas.'})

    return render(request, 'login.html')

def web_verificar_2fa(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        code = request.POST.get('code')
        try:
            user = Usuario.objects.get(id=user_id)
            if code and len(code) == 6:
                login(request, user)
                RegistroAuditoria.objects.create(
                    usuario=user, accion='VERIFICACION_2FA', entidad='Usuario',
                    identificador_registro=str(user.id),
                    ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
                )
                if user.rol == Usuario.Rol.FUNCIONARIO:
                    return redirect('web_personal')
                return redirect('web_dashboard')
            else:
                return render(request, 'login.html', {'show_2fa': True, 'user_id': user_id, 'error': 'Código 2FA incorrecto.'})
        except Usuario.DoesNotExist:
            return redirect('web_login')
    return redirect('web_login')

def web_logout(request):
    logout(request)
    return redirect('web_login')

def web_dashboard(request):
    periodo = PeriodoMedicion.objects.filter(cerrado=False).first() or PeriodoMedicion.objects.first()
    delegaciones = Delegacion.objects.filter(activo=True)
    
    del_id_param = request.GET.get('delegacion_id')
    delegacion_seleccionada = None
    if del_id_param:
        try:
            delegacion_seleccionada = int(del_id_param)
        except ValueError:
            pass

    comunal = calcular_resumen_comunal(periodo) if periodo else None
    
    if delegacion_seleccionada and comunal:
        delegaciones_filtradas = [d for d in comunal['delegaciones'] if d['delegacion_id'] == delegacion_seleccionada]
    else:
        delegaciones_filtradas = comunal['delegaciones'] if comunal else []

    total_funcionarios = sum(d['total_funcionarios'] for d in delegaciones_filtradas)
    total_pendientes_check = sum(d['evidencias_pendientes_check'] for d in delegaciones_filtradas)
    total_vencidos = sum(d['compromisos']['vencidos'] for d in delegaciones_filtradas)
    
    if delegaciones_filtradas:
        promedio_ponderado = round(sum(d['promedio_ponderado_pct'] for d in delegaciones_filtradas) / len(delegaciones_filtradas), 1)
    else:
        promedio_ponderado = 0.0

    meta_esp = comunal['meta_esperada_pct'] if comunal else 0.0
    semaforo_promedio = determinar_color_semaforo(promedio_ponderado, meta_esp)
    
    funcionarios_lista = []
    for d in delegaciones_filtradas:
        funcionarios_lista.extend(d['funcionarios'])

    return render(request, 'dashboard_general.html', {
        'comunal': comunal,
        'delegaciones': delegaciones,
        'delegacion_seleccionada': delegacion_seleccionada,
        'total_funcionarios': total_funcionarios,
        'total_pendientes_check': total_pendientes_check,
        'total_vencidos': total_vencidos,
        'promedio_ponderado': promedio_ponderado,
        'semaforo_promedio': semaforo_promedio,
        'funcionarios_lista': funcionarios_lista,
    })

def web_personal(request):
    periodo = PeriodoMedicion.objects.filter(cerrado=False).first() or PeriodoMedicion.objects.first()
    todos_funcionarios = Usuario.objects.filter(rol=Usuario.Rol.FUNCIONARIO, is_active=True)
    
    id_param = request.GET.get('id')
    funcionario = None
    if id_param:
        funcionario = Usuario.objects.filter(id=id_param).first()
    elif request.user.is_authenticated and request.user.rol == Usuario.Rol.FUNCIONARIO:
        funcionario = request.user
    elif todos_funcionarios.exists():
        funcionario = todos_funcionarios.first()

    metricas = None
    if funcionario and periodo:
        metricas = calcular_metricas_funcionario(funcionario, periodo)

    return render(request, 'dashboard_personal.html', {
        'funcionario': funcionario,
        'todos_funcionarios': todos_funcionarios,
        'metricas': metricas,
    })

def web_verificacion(request):
    delegaciones = Delegacion.objects.filter(activo=True)
    delegacion_filtro = request.GET.get('delegacion_id')
    estado_filtro = request.GET.get('estado', 'PENDIENTE')

    evidencias = Evidencia.objects.all().select_related('actividad__delegacion', 'actividad__funcionario', 'verificador').order_by('-fecha_subida')

    if delegacion_filtro:
        try:
            evidencias = evidencias.filter(actividad__delegacion_id=int(delegacion_filtro))
        except ValueError:
            pass

    if estado_filtro and estado_filtro != 'TODOS':
        evidencias = evidencias.filter(estado=estado_filtro)

    return render(request, 'verificacion_check.html', {
        'evidencias': evidencias,
        'delegaciones': delegaciones,
        'delegacion_filtro': int(delegacion_filtro) if delegacion_filtro else None,
        'estado_filtro': estado_filtro,
    })

def web_validar_evidencia(request, evidencia_id):
    if not request.user.is_authenticated or request.user.rol not in [Usuario.Rol.DELEGADO, Usuario.Rol.COORDINADOR, Usuario.Rol.ADMIN]:
        messages.error(request, "Acceso denegado: Un funcionario no puede auto-aprobar evidencias. Solo Delegados Municipales, Coordinadores y Administradores tienen facultades de validación (Regla RN-009 y Criterio CA-07).")
        return redirect('web_verificacion')

    if request.method == 'POST':
        evidencia = get_object_or_404(Evidencia, id=evidencia_id)
        decision = request.POST.get('decision')
        observacion = request.POST.get('observacion', '')

        # Si es Delegado, verificar que la evidencia pertenezca a su delegación
        if request.user.rol == Usuario.Rol.DELEGADO and request.user.delegacion:
            if evidencia.actividad.delegacion_id != request.user.delegacion_id:
                messages.error(request, f"Acceso restringido: Solo puedes validar evidencias de tu delegación ({request.user.delegacion.nombre}).")
                return redirect('web_verificacion')

        if decision in Evidencia.Estado.values:
            ant_est = evidencia.estado
            evidencia.estado = decision
            evidencia.observacion = observacion
            evidencia.verificador = request.user
            evidencia.fecha_validacion = timezone.now()
            evidencia.save()

            RegistroAuditoria.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                accion='VALIDAR_EVIDENCIA', entidad='Evidencia',
                identificador_registro=str(evidencia.id),
                valor_anterior={'estado': ant_est},
                valor_nuevo={'estado': decision, 'observacion': observacion, 'codigo': evidencia.codigo_verificador},
                ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
            messages.success(request, f"Evidencia {evidencia.codigo_verificador} validada como {evidencia.get_estado_display()}.")

    return redirect('web_verificacion')

def web_tubo(request):
    delegaciones = Delegacion.objects.filter(activo=True)
    usuarios_terreno = Usuario.objects.filter(is_active=True)
    hoy = timezone.now().date()

    compromisos = CompromisoAgenda.objects.all().select_related('delegacion', 'responsable').order_by('fecha_comprometida')

    return render(request, 'tubo_trabajo.html', {
        'delegaciones': delegaciones,
        'usuarios_terreno': usuarios_terreno,
        'hoy': hoy,
        'ingresados': compromisos.filter(estado=CompromisoAgenda.Estado.INGRESADO),
        'pendientes': compromisos.filter(estado=CompromisoAgenda.Estado.PENDIENTE),
        'en_proceso': compromisos.filter(estado=CompromisoAgenda.Estado.EN_PROCESO),
        'realizados': compromisos.filter(estado=CompromisoAgenda.Estado.REALIZADO),
    })

def web_cambiar_estado_compromiso(request, compromiso_id):
    if not request.user.is_authenticated:
        messages.error(request, "Debe iniciar sesión para modificar el estado de un compromiso.")
        return redirect('web_login')

    if request.method == 'POST':
        compromiso = get_object_or_404(CompromisoAgenda, id=compromiso_id)
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in CompromisoAgenda.Estado.values:
            ant = compromiso.estado
            compromiso.estado = nuevo_estado
            compromiso.save()
            RegistroAuditoria.objects.create(
                usuario=request.user,
                accion='CAMBIO_ESTADO', entidad='CompromisoAgenda',
                identificador_registro=str(compromiso.id),
                valor_anterior={'estado': ant},
                valor_nuevo={'estado': nuevo_estado},
                ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
            messages.success(request, f"Compromiso #{compromiso.id} movido a {compromiso.get_estado_display()}.")
    return redirect('web_tubo')

def web_crear_compromiso(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debe iniciar sesión para registrar nuevos compromisos.")
        return redirect('web_login')

    if request.method == 'POST':
        solicitante = request.POST.get('solicitante')
        delegacion_id = request.POST.get('delegacion_id')
        responsable_id = request.POST.get('responsable_id')
        fecha_comp = request.POST.get('fecha_comprometida')
        area_apoyo = request.POST.get('area_apoyo', 'Operaciones')
        descripcion = request.POST.get('descripcion')

        c = CompromisoAgenda.objects.create(
            solicitante=solicitante,
            delegacion_id=delegacion_id,
            responsable_id=responsable_id,
            fecha_comprometida=fecha_comp,
            area_apoyo=area_apoyo,
            descripcion=descripcion,
            estado=CompromisoAgenda.Estado.EN_PROCESO,
            creado_por=request.user
        )
        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion='CREAR', entidad='CompromisoAgenda',
            identificador_registro=str(c.id),
            valor_nuevo={'solicitante': c.solicitante},
            ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )
        messages.success(request, "Nuevo compromiso guardado en el Tubo de Trabajo.")
    return redirect('web_tubo')

def web_terreno(request):
    if not request.user.is_authenticated:
        return redirect('web_login')

    periodo = PeriodoMedicion.objects.filter(cerrado=False).first() or PeriodoMedicion.objects.first()
    items_medicion = ItemMedicion.objects.filter(periodo=periodo, activo=True) if periodo else []
    return render(request, 'terreno_movil.html', {
        'items_medicion': items_medicion,
    })

def web_casos_sociales(request):
    casos = CasoSocial.objects.all().prefetch_related('atenciones').select_related('delegacion')
    return render(request, 'casos_sociales.html', {
        'casos': casos,
    })

def web_auditoria(request):
    if not request.user.is_authenticated or request.user.rol not in [Usuario.Rol.ADMIN, Usuario.Rol.COORDINADOR]:
        messages.warning(request, "Acceso restringido: El registro inmutable de auditoría está reservado para la Coordinación Comunal y Administradores (Seguridad RNF-008).")
        return redirect('web_dashboard')

    registros = RegistroAuditoria.objects.all().select_related('usuario')[:50]
    return render(request, 'auditoria.html', {
        'registros': registros,
    })
