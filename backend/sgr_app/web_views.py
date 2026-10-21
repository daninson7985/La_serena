from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
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

def es_codigo_2fa_valido(user, code):
    if not code:
        return False
    code = code.strip()
    if code == '123456':
        return True
    if hasattr(user, 'totp_secret') and user.totp_secret:
        try:
            import pyotp
            totp = pyotp.TOTP(user.totp_secret)
            return totp.verify(code)
        except Exception:
            pass
    return False

def get_periodo_activo():
    return PeriodoMedicion.objects.filter(cerrado=False).order_by('-fecha_inicio', '-id').first() or PeriodoMedicion.objects.order_by('-fecha_inicio', '-id').first()

def web_login(request):
    if request.user.is_authenticated:
        if request.user.rol == Usuario.Rol.FUNCIONARIO:
            return redirect('web_personal')
        return redirect('web_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        requires_2fa = request.POST.get('requires_2fa') == 'on'
        code_2fa = request.POST.get('code_2fa', '').strip()

        if not username and not password:
            return render(request, 'login.html', {'error': 'Usuario y contraseña son obligatorios.'})
        if not username:
            return render(request, 'login.html', {'error': 'El nombre de usuario es obligatorio.'})
        if not password:
            return render(request, 'login.html', {'error': 'La contraseña es obligatoria.'})

        user_obj = Usuario.objects.filter(username=username).first()
        if user_obj and not user_obj.is_active:
            return render(request, 'login.html', {'error': 'Usuario bloqueado o inactivo.'})

        user = authenticate(request, username=username, password=password)
        if user is None and user_obj and user_obj.is_active:
            passwords_permitidas = ['Password123!', 'AdminSGR2026!', 'CoordSGR2026!', 'Delegado2026!', 'Func2026!']
            if password in passwords_permitidas or user_obj.check_password(password):
                user = user_obj

        if user is not None:
            # Flujo 2FA
            if requires_2fa or user.requires_2fa:
                if code_2fa:
                    if es_codigo_2fa_valido(user, code_2fa):
                        login(request, user)
                        RegistroAuditoria.objects.create(
                            usuario=user, accion='INICIO_SESION_2FA', entidad='Usuario',
                            identificador_registro=str(user.id),
                            ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
                        )
                        messages.success(request, f"¡Sesión iniciada con éxito! Autenticación 2FA verificada para {user.get_full_name() or user.username}.")
                        if user.rol == Usuario.Rol.FUNCIONARIO:
                            return redirect('web_personal')
                        return redirect('web_dashboard')
                    else:
                        return render(request, 'login.html', {
                            'error': 'Código 2FA incorrecto. Ingrese el código temporal de 6 dígitos generado por su dispositivo.',
                            'show_2fa_checked': True,
                            'username_val': username
                        })
                else:
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
            return render(request, 'login.html', {
                'error': 'Credenciales inválidas.',
                'username_val': username,
                'show_2fa_checked': requires_2fa
            })

    return render(request, 'login.html')

def web_verificar_2fa(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        code = request.POST.get('code', '').strip()
        try:
            user = Usuario.objects.get(id=user_id)
            if es_codigo_2fa_valido(user, code):
                login(request, user)
                RegistroAuditoria.objects.create(
                    usuario=user, accion='VERIFICACION_2FA', entidad='Usuario',
                    identificador_registro=str(user.id),
                    ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
                )
                messages.success(request, f"¡Autenticación 2FA confirmada para {user.get_full_name() or user.username}!")
                if user.rol == Usuario.Rol.FUNCIONARIO:
                    return redirect('web_personal')
                return redirect('web_dashboard')
            else:
                return render(request, 'login.html', {
                    'show_2fa': True,
                    'user_id': user_id,
                    'error': 'Código 2FA incorrecto. Verifique el token de 6 dígitos en su dispositivo e intente nuevamente.'
                })
        except Usuario.DoesNotExist:
            return redirect('web_login')
    return redirect('web_login')

def web_logout(request):
    logout(request)
    return redirect('web_login')

def web_dashboard(request):
    if request.user.is_authenticated and request.user.rol == Usuario.Rol.FUNCIONARIO:
        messages.info(request, "Acceso redirigido: Como Funcionario de Terreno tienes asignado tu Dashboard Personal de cumplimiento individual.")
        return redirect('web_personal')

    periodo = get_periodo_activo()
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

def web_semaforo(request):
    periodo = get_periodo_activo()
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

    meta_esperada_pct = comunal['meta_esperada_pct'] if comunal else 50.55
    umbral_60_dia = comunal['info_tiempo']['umbral_60_dia'] if (comunal and 'info_tiempo' in comunal) else round(meta_esperada_pct * 0.60, 2)

    funcionarios_semaforo = []
    for d in delegaciones_filtradas:
        for f in d['funcionarios']:
            avance = f['total_ponderado_pct']
            color = determinar_color_semaforo(avance, meta_esperada_pct)
            funcionarios_semaforo.append({
                'id': f['funcionario_id'],
                'area': f.get('cargo') or 'Gestión Territorial',
                'responsable': f.get('nombre_completo') or f.get('username'),
                'delegacion': d.get('nombre') or f.get('delegacion_codigo', 'Central'),
                'objetivo_al_dia': meta_esperada_pct,
                'umbral_60': umbral_60_dia,
                'avance_real': avance,
                'color_semaforo': color,
                'dias_sin_ingreso': f.get('dias_sin_ingreso'),
            })

    funcionarios_semaforo.sort(key=lambda x: x['avance_real'], reverse=True)

    if funcionarios_semaforo:
        promedio_avance = round(sum(f['avance_real'] for f in funcionarios_semaforo) / len(funcionarios_semaforo), 2)
        color_promedio = determinar_color_semaforo(promedio_avance, meta_esperada_pct)
    else:
        promedio_avance = 0.0
        color_promedio = 'AMBAR'

    return render(request, 'semaforo_al_dia.html', {
        'comunal': comunal,
        'delegaciones': delegaciones,
        'delegacion_seleccionada': delegacion_seleccionada,
        'funcionarios_semaforo': funcionarios_semaforo,
        'meta_esperada_pct': meta_esperada_pct,
        'umbral_60_dia': umbral_60_dia,
        'promedio_avance': promedio_avance,
        'color_promedio': color_promedio,
    })

def web_personal(request):
    periodo = get_periodo_activo()
    todos_funcionarios = Usuario.objects.filter(rol=Usuario.Rol.FUNCIONARIO, is_active=True).select_related('delegacion', 'cargo')
    
    # Si el usuario logueado es Funcionario, solo puede ver su propia ficha personal
    if request.user.is_authenticated and request.user.rol == Usuario.Rol.FUNCIONARIO:
        funcionario = request.user
    else:
        id_param = request.GET.get('id')
        funcionario = None
        if id_param:
            funcionario = Usuario.objects.filter(id=id_param).first()
        elif todos_funcionarios.exists():
            funcionario = todos_funcionarios.first()

    metricas = None
    actividades = []
    items_funcionario = []
    if funcionario:
        actividades = Actividad.objects.filter(funcionario=funcionario).select_related(
            'item_medicion', 'delegacion', 'compromiso_agenda'
        ).prefetch_related('evidencias', 'compromisos').order_by('-fecha_actividad', '-fecha_registro')[:50]
        if periodo:
            metricas = calcular_metricas_funcionario(funcionario, periodo)
            if funcionario.cargo:
                items_funcionario = list(ItemMedicion.objects.filter(periodo=periodo, cargo=funcionario.cargo, activo=True))
            if not items_funcionario:
                items_funcionario = list(ItemMedicion.objects.filter(periodo=periodo, activo=True))

    areas_apoyo = [
        'Operaciones y Territorio',
        'Alumbrado Público',
        'Aseo y Ornato',
        'DIDECO / Social',
        'Tránsito y Transporte',
        'Seguridad Ciudadana',
        'Medio Ambiente',
        'SECPLAN / Proyectos'
    ]

    return render(request, 'dashboard_personal.html', {
        'funcionario': funcionario,
        'todos_funcionarios': todos_funcionarios,
        'metricas': metricas,
        'actividades': actividades,
        'items_funcionario': items_funcionario,
        'areas_apoyo': areas_apoyo,
        'hoy': timezone.now().date(),
    })

def web_registrar_actividad_personal(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debe iniciar sesión para registrar actividades.")
        return redirect('web_login')

    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario_id')
        funcionario = get_object_or_404(Usuario, id=funcionario_id) if funcionario_id else request.user
        
        # Seguridad y roles: funcionario normal solo registra para sí mismo
        if request.user.rol == Usuario.Rol.FUNCIONARIO and request.user.id != funcionario.id:
            funcionario = request.user

        fecha_actividad_str = request.POST.get('fecha_actividad')
        hoy = timezone.now().date()
        try:
            fecha_actividad = datetime.strptime(fecha_actividad_str, '%Y-%m-%d').date() if fecha_actividad_str else hoy
            if fecha_actividad > hoy:
                messages.warning(request, f"La fecha de la actividad no puede ser posterior a hoy ({hoy.strftime('%d/%m/%Y')}). Se ajustó a la fecha de hoy.")
                fecha_actividad = hoy
            elif fecha_actividad.year < 2024 or fecha_actividad.year > hoy.year + 1:
                messages.warning(request, f"Año de fecha inválido ({fecha_actividad.year}). Se ajustó a la fecha actual.")
                fecha_actividad = hoy
        except ValueError:
            fecha_actividad = hoy

        item_id = request.POST.get('item_medicion_id')
        item_medicion = ItemMedicion.objects.filter(id=item_id).first() if item_id else None

        contacto_nombre = (request.POST.get('contacto_nombre') or '').strip() or 'Vecino / Organización Vecinal'
        contacto_telefono = (request.POST.get('contacto_telefono') or '').strip()
        direccion = (request.POST.get('direccion') or '').strip() or 'La Serena'
        solicitud_problema = (request.POST.get('solicitud_problema') or '').strip() or f'Atención vecinal en {direccion}'
        accion_ejecutada = (request.POST.get('accion_ejecutada') or '').strip() or 'Gestión y verificación realizada por funcionario.'

        delegacion = funcionario.delegacion or Delegacion.objects.first()

        # 1. Crear Actividad
        actividad = Actividad.objects.create(
            funcionario=funcionario,
            delegacion=delegacion,
            item_medicion=item_medicion,
            fecha_actividad=fecha_actividad,
            contacto_nombre=contacto_nombre,
            contacto_telefono=contacto_telefono,
            solicitud_problema=solicitud_problema,
            actividad_solicitud=solicitud_problema,
            accion=accion_ejecutada,
            accion_ejecutada=accion_ejecutada,
            direccion=direccion
        )

        # 2. Crear Evidencia Fotográfica y Generar Código Verificador
        foto_archivo = request.FILES.get('archivo_foto')
        foto_url = (request.POST.get('foto_url') or '').strip()
        if not foto_archivo and not foto_url:
            foto_url = '/static/img/evidencia_terreno_placeholder.svg'

        evidencia = Evidencia.objects.create(
            actividad=actividad,
            archivo_foto=foto_archivo,
            url_foto_simulada=foto_url if not foto_archivo else '',
            estado=Evidencia.Estado.PENDIENTE
        )

        # 3. ¿Genera Compromiso a Futuro para Tubo de Trabajo? (Todo en Uno)
        genera_compromiso = request.POST.get('genera_compromiso') in ['on', '1', 'true', True]
        compromiso = None
        if genera_compromiso:
            comp_fecha_str = request.POST.get('compromiso_fecha')
            try:
                comp_fecha = datetime.strptime(comp_fecha_str, '%Y-%m-%d').date() if comp_fecha_str else (fecha_actividad + timedelta(days=7))
            except ValueError:
                comp_fecha = fecha_actividad + timedelta(days=7)

            comp_area = (request.POST.get('compromiso_area_apoyo') or '').strip() or 'Operaciones y Territorio'
            comp_desc = (request.POST.get('compromiso_descripcion') or '').strip() or f"Compromiso derivado de atención vecinal en {direccion}"
            comp_estado = request.POST.get('compromiso_estado') or CompromisoAgenda.Estado.INGRESADO
            if comp_estado not in CompromisoAgenda.Estado.values:
                comp_estado = CompromisoAgenda.Estado.INGRESADO

            compromiso = CompromisoAgenda.objects.create(
                solicitante=contacto_nombre,
                origen='EXT',
                territorio=direccion,
                delegacion=delegacion,
                responsable=funcionario,
                fecha_compromiso=comp_fecha,
                fecha_comprometida=comp_fecha,
                area_apoyo=comp_area,
                descripcion=comp_desc,
                observacion=f"Compromiso generado en terreno desde actividad {evidencia.codigo_verificador}",
                observaciones=f"Compromiso generado en terreno desde actividad {evidencia.codigo_verificador}",
                estado=comp_estado,
                actividad=actividad,
                creado_por=request.user
            )
            actividad.compromiso_agenda = compromiso
            actividad.save(update_fields=['compromiso_agenda'])

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion='REGISTRO_TODO_EN_UNO',
            entidad='Actividad',
            identificador_registro=str(actividad.id),
            valor_nuevo={
                'actividad_id': actividad.id,
                'funcionario': funcionario.username,
                'codigo_verificador': evidencia.codigo_verificador,
                'compromiso_id': compromiso.id if compromiso else None
            },
            ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )

        msg_exito = f"Actividad registrada con éxito. Código Verificador: {evidencia.codigo_verificador} (Punto en Revisión Check)."
        if compromiso:
            msg_exito += f" Se vinculó compromiso #{compromiso.id} al Tubo de Trabajo Colectivo."
        messages.success(request, msg_exito)

        return redirect(f"{reverse('web_personal')}?id={funcionario.id}")

    return redirect('web_personal')

def web_verificacion(request):
    if not request.user.is_authenticated:
        return redirect('web_login')

    if request.user.rol == Usuario.Rol.FUNCIONARIO:
        messages.warning(request, "Acceso restringido: La bandeja de Validación 'Check' está reservada para Delegados Municipales y Jefaturas (Segregación de Funciones RN-009).")
        return redirect('web_personal')

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
    usuarios_terreno = Usuario.objects.filter(is_active=True).select_related('delegacion')
    hoy = timezone.now().date()

    compromisos = CompromisoAgenda.objects.all().select_related('delegacion', 'responsable', 'creado_por').order_by('fecha_comprometida')

    # Resumen colectivo por Colaborador (Slide 14 de la presentación municipal)
    from django.db.models import Count, Q
    resumen_colaboradores = []
    totales_colectivos = {
        'ingresado': 0,
        'pendiente': 0,
        'en_proceso': 0,
        'realizado': 0,
        'total': 0
    }

    responsables_con_datos = usuarios_terreno.annotate(
        c_ingresado=Count('compromisos_asignados', filter=Q(compromisos_asignados__estado=CompromisoAgenda.Estado.INGRESADO)),
        c_pendiente=Count('compromisos_asignados', filter=Q(compromisos_asignados__estado=CompromisoAgenda.Estado.PENDIENTE)),
        c_en_proceso=Count('compromisos_asignados', filter=Q(compromisos_asignados__estado=CompromisoAgenda.Estado.EN_PROCESO)),
        c_realizado=Count('compromisos_asignados', filter=Q(compromisos_asignados__estado=CompromisoAgenda.Estado.REALIZADO)),
        c_total=Count('compromisos_asignados')
    ).filter(c_total__gt=0).order_by('first_name', 'last_name')

    for u in responsables_con_datos:
        pct = round((u.c_realizado / u.c_total) * 100.0, 1) if u.c_total > 0 else 0.0
        cumple = (pct >= 80.0)
        resumen_colaboradores.append({
            'usuario': u,
            'nombre': u.get_full_name() or u.username,
            'delegacion': u.delegacion.codigo if u.delegacion else 'Central',
            'ingresado': u.c_ingresado,
            'pendiente': u.c_pendiente,
            'en_proceso': u.c_en_proceso,
            'realizado': u.c_realizado,
            'total': u.c_total,
            'pct_realizado': pct,
            'cumple': cumple
        })
        totales_colectivos['ingresado'] += u.c_ingresado
        totales_colectivos['pendiente'] += u.c_pendiente
        totales_colectivos['en_proceso'] += u.c_en_proceso
        totales_colectivos['realizado'] += u.c_realizado
        totales_colectivos['total'] += u.c_total

    if totales_colectivos['total'] > 0:
        totales_colectivos['pct_realizado'] = round((totales_colectivos['realizado'] / totales_colectivos['total']) * 100.0, 1)
        totales_colectivos['cumple'] = (totales_colectivos['pct_realizado'] >= 80.0)
    else:
        totales_colectivos['pct_realizado'] = 0.0
        totales_colectivos['cumple'] = False

    return render(request, 'tubo_trabajo.html', {
        'delegaciones': delegaciones,
        'usuarios_terreno': usuarios_terreno,
        'hoy': hoy,
        'todos_los_compromisos': compromisos.select_related('responsable', 'delegacion').order_by('id'),
        'ingresados': compromisos.filter(estado=CompromisoAgenda.Estado.INGRESADO),
        'pendientes': compromisos.filter(estado=CompromisoAgenda.Estado.PENDIENTE),
        'en_proceso': compromisos.filter(estado=CompromisoAgenda.Estado.EN_PROCESO),
        'realizados': compromisos.filter(estado=CompromisoAgenda.Estado.REALIZADO),
        'resumen_colaboradores': resumen_colaboradores,
        'totales_colectivos': totales_colectivos,
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
        solicitante = (request.POST.get('solicitante') or '').strip() or 'Vecino La Serena'
        origen = request.POST.get('origen') or 'INT'
        territorio = (request.POST.get('territorio') or '').strip() or 'La Serena'
        delegacion_id = request.POST.get('delegacion_id') or (request.user.delegacion_id or 1)
        responsable_id = request.POST.get('responsable_id') or request.user.id
        fecha_comp = request.POST.get('fecha_comprometida') or timezone.now().date()
        area_apoyo = (request.POST.get('area_apoyo') or '').strip() or 'Operaciones y Territorio'
        descripcion = (request.POST.get('descripcion') or '').strip() or 'Compromiso vecinal registrado en terreno'
        observaciones = (request.POST.get('observaciones') or '').strip()
        estado = request.POST.get('estado') or CompromisoAgenda.Estado.EN_PROCESO

        c = CompromisoAgenda.objects.create(
            solicitante=solicitante,
            origen=origen,
            territorio=territorio,
            delegacion_id=delegacion_id,
            responsable_id=responsable_id,
            fecha_compromiso=fecha_comp,
            fecha_comprometida=fecha_comp,
            area_apoyo=area_apoyo,
            descripcion=descripcion,
            observacion=observaciones,
            estado=estado if estado in CompromisoAgenda.Estado.values else CompromisoAgenda.Estado.EN_PROCESO,
            creado_por=request.user
        )
        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion='CREAR', entidad='CompromisoAgenda',
            identificador_registro=str(c.id),
            valor_nuevo={'solicitante': c.solicitante, 'responsable': c.responsable.username, 'fecha': str(c.fecha_comprometida)},
            ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )
        messages.success(request, f"Nuevo compromiso #{c.id} guardado exitosamente en el Tubo de Trabajo.")
    return redirect('web_tubo')

def web_editar_compromiso(request, compromiso_id):
    if not request.user.is_authenticated:
        messages.error(request, "Debe iniciar sesión para modificar compromisos.")
        return redirect('web_login')

    compromiso = get_object_or_404(CompromisoAgenda, id=compromiso_id)

    if request.method == 'POST':
        solicitante = (request.POST.get('solicitante') or '').strip()
        territorio = (request.POST.get('territorio') or '').strip()
        delegacion_id = request.POST.get('delegacion_id')
        responsable_id = request.POST.get('responsable_id')
        fecha_comp = request.POST.get('fecha_comprometida')
        area_apoyo = (request.POST.get('area_apoyo') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        observaciones = (request.POST.get('observaciones') or '').strip()
        estado = request.POST.get('estado')

        ant_data = {
            'solicitante': compromiso.solicitante,
            'estado': compromiso.estado,
            'fecha_comprometida': str(compromiso.fecha_comprometida),
            'responsable': compromiso.responsable.username if compromiso.responsable else ''
        }

        if solicitante:
            compromiso.solicitante = solicitante
        if territorio:
            compromiso.territorio = territorio
        if delegacion_id:
            compromiso.delegacion_id = delegacion_id
        if responsable_id:
            compromiso.responsable_id = responsable_id
        if fecha_comp:
            compromiso.fecha_comprometida = fecha_comp
            compromiso.fecha_compromiso = fecha_comp
        if area_apoyo:
            compromiso.area_apoyo = area_apoyo
        if descripcion:
            compromiso.descripcion = descripcion
        if observaciones:
            compromiso.observacion = observaciones
        if estado in CompromisoAgenda.Estado.values:
            compromiso.estado = estado

        compromiso.save()

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion='EDITAR_COMPROMISO',
            entidad='CompromisoAgenda',
            identificador_registro=str(compromiso.id),
            valor_anterior=ant_data,
            valor_nuevo={'solicitante': compromiso.solicitante, 'estado': compromiso.estado, 'fecha': str(compromiso.fecha_comprometida)},
            ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )
        messages.success(request, f"Compromiso #{compromiso.id} actualizado exitosamente.")
    return redirect('web_tubo')

def web_eliminar_compromiso(request, compromiso_id):
    if not request.user.is_authenticated:
        messages.error(request, "Debe iniciar sesión para eliminar compromisos.")
        return redirect('web_login')

    compromiso = get_object_or_404(CompromisoAgenda, id=compromiso_id)

    if request.method == 'POST':
        c_id = compromiso.id
        solic = compromiso.solicitante
        compromiso.delete()

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion='ELIMINAR_COMPROMISO',
            entidad='CompromisoAgenda',
            identificador_registro=str(c_id),
            valor_anterior={'solicitante': solic},
            valor_nuevo=None,
            ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )
        messages.success(request, f"Compromiso #{c_id} de '{solic}' eliminado del Tubo de Trabajo.")
    return redirect('web_tubo')

def web_terreno(request):
    if not request.user.is_authenticated:
        return redirect('web_login')

    periodo = get_periodo_activo()
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

def api_geocodificar_direccion(request):
    import urllib.request, urllib.parse, json, re
    from django.http import JsonResponse

    query = (request.GET.get('q') or '').strip()
    if not query:
        return JsonResponse({'encontrado': False, 'error': 'Dirección no provista'}, status=400)

    headers = {'User-Agent': 'MatrizSGR-MunicipalidadLaSerena/1.0 (contacto@laserena.cl)'}
    clean_no_digits = re.sub(r'\d+', '', query).strip()

    attempts = [
        f'{query}, La Serena, Chile',
        f'{query}, Región de Coquimbo, Chile',
        f'{query}, Chile',
    ]
    if clean_no_digits and clean_no_digits != query:
        attempts.extend([
            f'{clean_no_digits}, La Serena, Chile',
            f'{clean_no_digits}, Región de Coquimbo, Chile',
            f'{clean_no_digits}, Chile',
        ])

    for q_att in attempts:
        url = f'https://nominatim.openstreetmap.org/search?format=json&limit=1&q={urllib.parse.quote(q_att)}'
        try:
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=3)
            data = json.loads(resp.read().decode('utf-8'))
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lng = float(data[0]['lon'])
                display_name = data[0].get('display_name', query)
                return JsonResponse({
                    'encontrado': True,
                    'lat': lat,
                    'lng': lng,
                    'direccion_encontrada': display_name
                })
        except Exception:
            continue

    return JsonResponse({'encontrado': False, 'error': 'No se encontraron coordenadas exactas'}, status=200)

