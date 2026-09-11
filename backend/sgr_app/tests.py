from datetime import date, timedelta
from django.test import TestCase, Client
from django.utils import timezone
from sgr_app.models import (
    Delegacion, Cargo, Usuario, PeriodoMedicion, ItemMedicion,
    Actividad, Evidencia, CompromisoAgenda, CasoSocial, AtencionSocial,
    RegistroAuditoria, generar_codigo_evidencia
)
from sgr_app.services.calculos import (
    calcular_dias_periodo,
    determinar_color_semaforo,
    calcular_metricas_funcionario,
    calcular_resumen_delegacion,
    calcular_resumen_comunal
)

class MatrizSGRTestSuite(TestCase):
    def setUp(self):
        self.delegacion = Delegacion.objects.create(nombre="Las Compañías", codigo="CIA")
        self.cargo = Cargo.objects.create(nombre="Gestor Territorial")
        self.usuario = Usuario.objects.create_user(
            username="carlos.test",
            password="Password123!",
            rol=Usuario.Rol.FUNCIONARIO,
            cargo=self.cargo,
            delegacion=self.delegacion,
            first_name="Carlos",
            last_name="Tapia"
        )
        self.verificador = Usuario.objects.create_user(
            username="pablo.cuadra",
            password="Password123!",
            rol=Usuario.Rol.DELEGADO,
            cargo=self.cargo,
            delegacion=self.delegacion,
            first_name="Pablo",
            last_name="Cuadra"
        )
        self.periodo = PeriodoMedicion.objects.create(
            nombre="T3 Test 2026",
            fecha_inicio=date(2026, 7, 1),
            fecha_termino=date(2026, 9, 30),
            tope_cumplimiento=150.0
        )
        # Ítems que suman 100% de ponderación (RN-001)
        self.item1 = ItemMedicion.objects.create(
            cargo=self.cargo, periodo=self.periodo,
            nombre_item="Operativos Terreno", meta_cuantitativa=10.0, ponderador=60.0
        )
        self.item2 = ItemMedicion.objects.create(
            cargo=self.cargo, periodo=self.periodo,
            nombre_item="Atención Solicitudes", meta_cuantitativa=5.0, ponderador=40.0
        )

    # 1. Reglas de Cálculo del Semáforo y Días Computables (RN-007, RN-008)
    def test_dias_computables_y_meta_esperada(self):
        fecha_mitad = date(2026, 8, 15)
        res = calcular_dias_periodo(self.periodo, fecha_mitad)
        self.assertEqual(res['dias_totales'], 92)
        self.assertTrue(0 < res['meta_esperada_pct'] < 100)

    def test_clasificacion_semaforo(self):
        # Verde si avance >= meta esperada
        self.assertEqual(determinar_color_semaforo(50.0, 50.0), 'VERDE')
        self.assertEqual(determinar_color_semaforo(60.0, 50.0), 'VERDE')
        # Ámbar si avance >= 60% de lo esperado y < esperado
        self.assertEqual(determinar_color_semaforo(35.0, 50.0), 'AMBAR')
        self.assertEqual(determinar_color_semaforo(30.0, 50.0), 'AMBAR')
        # Rojo si avance < 60% de lo esperado
        self.assertEqual(determinar_color_semaforo(25.0, 50.0), 'ROJO')

    # 2. Criterio CA-01 y CA-02: Validación de Evidencia Aprobada vs Rechazada
    def test_ca01_ca02_validacion_evidencia(self):
        act = Actividad.objects.create(
            funcionario=self.usuario, delegacion=self.delegacion,
            item_medicion=self.item1, actividad_solicitud="Bacheo pasaje",
            accion_ejecutada="Reparado", fecha_actividad=date(2026, 8, 1)
        )
        ev = Evidencia.objects.create(actividad=act, estado=Evidencia.Estado.PENDIENTE)

        # Pendiente: avance es 0
        m1 = calcular_metricas_funcionario(self.usuario, self.periodo, date(2026, 8, 15))
        item_data = next(i for i in m1['items'] if i['item_id'] == self.item1.id)
        self.assertEqual(item_data['avance_aprobado'], 0)

        # CA-01: Aprobar evidencia aumenta avance a 1
        ev.estado = Evidencia.Estado.APROBADA
        ev.verificador = self.verificador
        ev.save()

        m2 = calcular_metricas_funcionario(self.usuario, self.periodo, date(2026, 8, 15))
        item_data2 = next(i for i in m2['items'] if i['item_id'] == self.item1.id)
        self.assertEqual(item_data2['avance_aprobado'], 1)
        self.assertEqual(item_data2['cumplimiento_pct'], 10.0)

        # CA-02: Rechazar evidencia con observación no suma y conserva motivo
        ev.estado = Evidencia.Estado.RECHAZADA
        ev.observacion = "Foto no nítida"
        ev.save()

        m3 = calcular_metricas_funcionario(self.usuario, self.periodo, date(2026, 8, 15))
        item_data3 = next(i for i in m3['items'] if i['item_id'] == self.item1.id)
        self.assertEqual(item_data3['avance_aprobado'], 0)
        self.assertEqual(ev.observacion, "Foto no nítida")

    # 3. Criterio CA-03: Compromisos Vencidos en Tubo de Trabajo
    def test_ca03_compromiso_vencido(self):
        hoy = timezone.now().date()
        ayer = hoy - timedelta(days=1)
        manana = hoy + timedelta(days=2)

        comp_vencido = CompromisoAgenda.objects.create(
            solicitante="Vecino A", delegacion=self.delegacion,
            responsable=self.usuario, fecha_comprometida=ayer,
            descripcion="Plaza", estado=CompromisoAgenda.Estado.EN_PROCESO
        )
        comp_al_dia = CompromisoAgenda.objects.create(
            solicitante="Vecino B", delegacion=self.delegacion,
            responsable=self.usuario, fecha_comprometida=manana,
            descripcion="Luminaria", estado=CompromisoAgenda.Estado.EN_PROCESO
        )

        resumen = calcular_resumen_delegacion(self.delegacion, self.periodo)
        self.assertEqual(resumen['compromisos']['vencidos'], 1)
        self.assertEqual(resumen['compromisos']['total'], 2)

    # 4. Regla RN-005: Cumplimiento Ponderado con Tope Máximo 150%
    def test_rn005_tope_maximo_cumplimiento(self):
        # Meta es 10 actividades. Registramos 20 actividades aprobadas (200%)
        for i in range(20):
            act = Actividad.objects.create(
                funcionario=self.usuario, delegacion=self.delegacion,
                item_medicion=self.item1, actividad_solicitud=f"Actividad {i}",
                accion_ejecutada="Ejecutada", fecha_actividad=date(2026, 8, 1)
            )
            Evidencia.objects.create(actividad=act, estado=Evidencia.Estado.APROBADA)

        metricas = calcular_metricas_funcionario(self.usuario, self.periodo, date(2026, 8, 15))
        it = next(i for i in metricas['items'] if i['item_id'] == self.item1.id)

        self.assertEqual(it['cumplimiento_pct'], 200.0)
        # Con tope de 150%, aporte ponderado = (60% * 150) / 100 = 90.0%
        self.assertEqual(it['aporte_ponderado'], 90.0)

    # 5. Código Único e Inmutable de Evidencia (RN-010, HU-10)
    def test_generador_codigo_evidencia(self):
        cod = generar_codigo_evidencia("CIA")
        self.assertTrue(cod.startswith("CIA"))
        self.assertEqual(len(cod), 9)

    # 6. Casos Sociales con Secuencia de 3 Etapas (RF-015, CA-04)
    def test_casos_sociales_secuencia_tres_etapas(self):
        caso = CasoSocial.objects.create(
            codigo_caso="CASO-TEST-001", persona_anonimizada="Persona Prueba",
            delegacion=self.delegacion
        )
        AtencionSocial.objects.create(caso=caso, etapa=1, tipo_atencion="Ficha", detalle="E1", resultado="OK", funcionario=self.usuario)
        AtencionSocial.objects.create(caso=caso, etapa=2, tipo_atencion="Visita", detalle="E2", resultado="OK", funcionario=self.usuario)
        AtencionSocial.objects.create(caso=caso, etapa=3, tipo_atencion="Cierre", detalle="E3", resultado="OK", funcionario=self.usuario)
        self.assertEqual(caso.atenciones.count(), 3)

    # 7. Auditoría de Operaciones Críticas (RF-036, CA-09, HU-30)
    def test_ca09_auditoria_operaciones(self):
        RegistroAuditoria.objects.create(
            usuario=self.usuario, accion='CREAR', entidad='Actividad',
            identificador_registro="101", valor_nuevo={'actividad': 'Nueva'}
        )
        self.assertEqual(RegistroAuditoria.objects.filter(identificador_registro="101").count(), 1)

    # 8. Verificación de Vistas Web y RBAC (HTTP 200 y control de acceso)
    def test_vistas_web_integrales(self):
        c = Client()
        # Login
        r_login = c.get('/')
        self.assertEqual(r_login.status_code, 200)

        # Autenticar como delegado
        c.force_login(self.verificador)

        for url in ['/dashboard/', '/personal/', '/verificacion/', '/tubo/', '/terreno/', '/casos-sociales/']:
            resp = c.get(url)
            self.assertEqual(resp.status_code, 200, f"Falla en {url}")

        # Delegado no debe acceder a auditoría (Segregación RNF-008, debe dar 302 redirect)
        resp_auditoria_del = c.get('/auditoria/')
        self.assertEqual(resp_auditoria_del.status_code, 302)

        # Admin sí puede acceder a auditoría (HTTP 200)
        admin_user = Usuario.objects.create_user(
            username='admin.test', password='password123',
            rol=Usuario.Rol.ADMIN
        )
        c.force_login(admin_user)
        resp_auditoria_admin = c.get('/auditoria/')
        self.assertEqual(resp_auditoria_admin.status_code, 200)

    # 10. Seguridad y Segregación de Funciones en API REST (RN-009, CA-07)
    def test_segregacion_funciones_api(self):
        c = Client()
        act = Actividad.objects.create(
            funcionario=self.usuario, delegacion=self.delegacion,
            item_medicion=self.item1, actividad_solicitud="Operativo Terreno",
            accion_ejecutada="Realizado", fecha_actividad=date(2026, 8, 1)
        )
        ev = Evidencia.objects.create(actividad=act, estado=Evidencia.Estado.PENDIENTE)

        # 1. Funcionario intenta auto-aprobarse -> Debe retornar HTTP 403 Forbidden
        c.force_login(self.usuario)
        resp_func = c.post(f"/api/evidencias/{ev.id}/validar/", {'decision': 'APROBADA'}, content_type='application/json')
        self.assertEqual(resp_func.status_code, 403)

        # 2. Delegado de su delegación aprueba -> Debe retornar HTTP 200 OK
        c.force_login(self.verificador)
        resp_del = c.post(f"/api/evidencias/{ev.id}/validar/", {'decision': 'APROBADA'}, content_type='application/json')
        self.assertEqual(resp_del.status_code, 200)
        ev.refresh_from_db()
        self.assertEqual(ev.estado, Evidencia.Estado.APROBADA)