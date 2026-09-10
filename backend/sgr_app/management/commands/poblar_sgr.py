import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from sgr_app.models import (
    Delegacion, Cargo, Usuario, PeriodoMedicion, CatalogoServicio,
    ItemMedicion, CompromisoAgenda, Actividad, Evidencia,
    CasoSocial, AtencionSocial, RegistroAuditoria
)

class Command(BaseCommand):
    help = 'Puebla la base de datos con datos institucionales oficiales y datos sintéticos anonimizados de La Serena'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando poblado de datos SGR..."))

        # 1. Delegaciones
        delegaciones_data = [
            {"nombre": "Avenida del Mar", "codigo": "ADM", "direccion": "Avenida del Mar 2500", "telefono": "512 206518", "email": "avenidadelmar@laserena.cl"},
            {"nombre": "Centro", "codigo": "CEN", "direccion": "Cienfuegos 226", "telefono": "512 207861", "email": "centro@laserena.cl"},
            {"nombre": "La Antena - La Florida", "codigo": "ANT", "direccion": "Avenida 18 de Septiembre S/N", "telefono": "512 206618", "email": "antena@laserena.cl"},
            {"nombre": "Las Compañías", "codigo": "CIA", "direccion": "Esmeralda 2422, Costado Banco Estado", "telefono": "512 206527", "email": "lascompanias@laserena.cl"},
            {"nombre": "La Pampa", "codigo": "PAM", "direccion": "Larraín Alcalde 3505", "telefono": "512 206788", "email": "pampa@laserena.cl"},
            {"nombre": "Rural", "codigo": "RUR", "direccion": "O'Higgins 154", "telefono": "512 206687", "email": "rural@laserena.cl"},
        ]
        dels = {}
        for d in delegaciones_data:
            obj, created = Delegacion.objects.get_or_create(
                codigo=d["codigo"],
                defaults={
                    "nombre": d["nombre"],
                    "direccion": d["direccion"],
                    "telefono": d["telefono"],
                    "email": d["email"],
                    "activo": True
                }
            )
            dels[d["codigo"]] = obj

        # 2. Cargos
        cargos_data = [
            ("Coordinador Comunal", "Supervisión global de las 6 delegaciones"),
            ("Delegado Municipal", "Jefatura territorial a cargo de la delegación y validación de evidencias"),
            ("Gestor Territorial", "Funcionario en terreno encargado de inspección, mediación y operativos"),
            ("Trabajador Social", "Atención ciudadana, estratificación y gestión de subsidios"),
            ("Administrativo de Atención", "Recepción y canalización de solicitudes ciudadanas"),
        ]
        cargos = {}
        for nombre, desc in cargos_data:
            c, _ = Cargo.objects.get_or_create(nombre=nombre, defaults={"descripcion": desc})
            cargos[nombre] = c

        # 3. Usuarios Institucionales
        # Administrador y Coordinador
        admin_u, _ = Usuario.objects.get_or_create(
            username="admin",
            defaults={"first_name": "Admin", "last_name": "Sistema", "email": "admin.sgr@laserena.cl", "rol": Usuario.Rol.ADMIN, "is_staff": True, "is_superuser": True}
        )
        admin_u.set_password("AdminSGR2026!")
        admin_u.save()

        coord_u, _ = Usuario.objects.get_or_create(
            username="coordinador",
            defaults={"first_name": "Coordinador", "last_name": "Comunal", "email": "coordinacion@laserena.cl", "rol": Usuario.Rol.COORDINADOR, "cargo": cargos["Coordinador Comunal"]}
        )
        coord_u.set_password("CoordSGR2026!")
        coord_u.save()

        # Delegados reales según documento
        delegados_data = [
            ("pablo.cuadra", "Pablo", "Cuadra Corrales", "lascompanias@laserena.cl", "CIA"),
            ("elizabeth.villanueva", "Elizabeth", "Villanueva Oyarce", "antena@laserena.cl", "ANT"),
            ("rodrigo.fuenzalida", "Rodrigo", "Fuenzalida Vásquez", "avenidadelmar@laserena.cl", "ADM"),
            ("alan.von", "Alan", "Von Kretschmann", "centro@laserena.cl", "CEN"),
            ("manuel.barraza", "Manuel", "Barraza Delgado", "rural@laserena.cl", "RUR"),
            ("soledad.rojas", "María Soledad", "Rojas", "pampa@laserena.cl", "PAM"),
        ]
        delegados_dict = {}
        for usr, fname, lname, email, cod_del in delegados_data:
            u, _ = Usuario.objects.get_or_create(
                username=usr,
                defaults={
                    "first_name": fname,
                    "last_name": lname,
                    "email": email,
                    "rol": Usuario.Rol.DELEGADO,
                    "cargo": cargos["Delegado Municipal"],
                    "delegacion": dels[cod_del]
                }
            )
            u.set_password("Delegado2026!")
            u.save()
            delegados_dict[cod_del] = u

        # Funcionarios en terreno
        funcionarios_data = [
            ("carlos.terreno.cia", "Carlos", "Tapia", "Gestor Territorial", "CIA"),
            ("ana.social.cia", "Ana", "Rojas", "Trabajador Social", "CIA"),
            ("javier.terreno.ant", "Javier", "Morales", "Gestor Territorial", "ANT"),
            ("patricia.social.ant", "Patricia", "Araya", "Trabajador Social", "ANT"),
            ("matias.dev", "Matías", "Gómez", "Gestor Territorial", "CIA"),
        ]
        funcionarios_dict = {}
        for usr, fname, lname, c_nom, cod_del in funcionarios_data:
            u, _ = Usuario.objects.get_or_create(
                username=usr,
                defaults={
                    "first_name": fname,
                    "last_name": lname,
                    "email": f"{usr}@laserena.cl",
                    "rol": Usuario.Rol.FUNCIONARIO,
                    "cargo": cargos[c_nom],
                    "delegacion": dels[cod_del]
                }
            )
            u.set_password("Terreno2026!")
            u.save()
            funcionarios_dict[usr] = u

        # 4. Periodo de Medición
        periodo, _ = PeriodoMedicion.objects.get_or_create(
            nombre="Trimestre 3 - 2026 (Julio - Septiembre)",
            defaults={
                "fecha_inicio": datetime.date(2026, 7, 1),
                "fecha_termino": datetime.date(2026, 9, 30),
                "dias_computables": 92,
                "cerrado": False,
                "umbral_colectivo": 80.0,
                "tope_cumplimiento": 150.0
            }
        )

        # 5. Catálogo de Servicios
        catalogos = [
            ("INF-01", "Reparación de Luminarias y Bacheo", "Obras y Servicios"),
            ("SOC-01", "Subsidio Social y Ayuda de Emergencia", "DIDECO / Social"),
            ("SEG-01", "Operativo de Prevención y Seguridad", "Seguridad Ciudadana"),
            ("MED-01", "Retiro de Microbasurales y Escombros", "Medio Ambiente"),
            ("TER-01", "Audiencia y Mediación Comunitaria", "Gestión Territorial"),
        ]
        cat_dict = {}
        for cod, nom, area in catalogos:
            cs, _ = CatalogoServicio.objects.get_or_create(codigo=cod, defaults={"nombre": nom, "area": area, "activo": True})
            cat_dict[cod] = cs

        # 6. Ítems de Medición (Suma de ponderadores = 100% por cargo)
        # Gestor Territorial
        items_gestor = [
            ("Operativos de Inspección Territorial", 60.0, 40.0, "Operativos"),
            ("Canalización de Solicitudes Vecinales", 45.0, 35.0, "Solicitudes"),
            ("Reuniones de Coordinación Comunitaria", 20.0, 25.0, "Reuniones"),
        ]
        items_g_objs = []
        for nom, meta, pond, uni in items_gestor:
            it, _ = ItemMedicion.objects.get_or_create(
                cargo=cargos["Gestor Territorial"],
                periodo=periodo,
                nombre_item=nom,
                defaults={"meta_cuantitativa": meta, "ponderador": pond, "unidad_medida": uni, "activo": True}
            )
            items_g_objs.append(it)

        # Trabajador Social
        items_social = [
            ("Estratificación y Fichas RSH", 50.0, 40.0, "Fichas"),
            ("Evaluación de Beneficios de Emergencia", 30.0, 30.0, "Evaluaciones"),
            ("Visitas Domiciliarias Terreno", 30.0, 30.0, "Visitas"),
        ]
        items_s_objs = []
        for nom, meta, pond, uni in items_social:
            it, _ = ItemMedicion.objects.get_or_create(
                cargo=cargos["Trabajador Social"],
                periodo=periodo,
                nombre_item=nom,
                defaults={"meta_cuantitativa": meta, "ponderador": pond, "unidad_medida": uni, "activo": True}
            )
            items_s_objs.append(it)

        # 7. Tubo de Trabajo (Compromisos Agenda Colectiva)
        compromisos_data = [
            ("Junta de Vecinos El Brillador", dels["CIA"], funcionarios_dict["carlos.terreno.cia"], datetime.date(2026, 9, 10), "Reparación luminaria plaza principal", CompromisoAgenda.Estado.EN_PROCESO),
            ("Comité de Adelanto Las Vertientes", dels["CIA"], funcionarios_dict["carlos.terreno.cia"], datetime.date(2026, 8, 20), "Limpieza canal vecinal de regadío", CompromisoAgenda.Estado.REALIZADO),
            ("Vecina Sector Esmeralda (Anonimizado)", dels["CIA"], funcionarios_dict["ana.social.cia"], datetime.date(2026, 8, 25), "Entrega canasta y pañales adulto mayor", CompromisoAgenda.Estado.REALIZADO),
            ("Unión Comunal La Antena", dels["ANT"], funcionarios_dict["javier.terreno.ant"], datetime.date(2026, 8, 15), "Inspección de baches en Av. 18 Septiembre", CompromisoAgenda.Estado.PENDIENTE), # Vencido
            ("Club Adulto Mayor Esperanza", dels["ANT"], funcionarios_dict["patricia.social.ant"], datetime.date(2026, 9, 18), "Taller de postulación Fondo Presidente de la República", CompromisoAgenda.Estado.INGRESADO),
        ]
        for sol, dl, resp, f_comp, desc, est in compromisos_data:
            CompromisoAgenda.objects.get_or_create(
                solicitante=sol,
                delegacion=dl,
                responsable=resp,
                fecha_comprometida=f_comp,
                defaults={"descripcion": desc, "estado": est, "area_apoyo": "Operaciones"}
            )

        # 8. Actividades y Evidencias (Códigos únicos alfanuméricos inmutables)
        # Actividades para Carlos Tapia (Las Compañías)
        actividades_carlos = [
            ("Inspección de luminarias Pasaje 3", "Se constata reposición de foco LED N° 4", items_g_objs[0], cat_dict["INF-01"], Evidencia.Estado.APROBADA, "CIA711", "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=600&q=80"),
            ("Revisión de bacheo calle México", "Asfaltado en frío completado con cuadrilla", items_g_objs[0], cat_dict["INF-01"], Evidencia.Estado.APROBADA, "CIA712", "https://images.unsplash.com/photo-1541888946425-d0fbb1861564?auto=format&fit=crop&w=600&q=80"),
            ("Inspección microbasural Av. Islón", "Fiscalización y notificación a predio", items_g_objs[0], cat_dict["MED-01"], Evidencia.Estado.APROBADA, "CIA713", "https://images.unsplash.com/photo-1530587191325-3db32d826c18?auto=format&fit=crop&w=600&q=80"),
            ("Recepción solicitud vecinal agua potable", "Toma de contacto con directiva rural", items_g_objs[1], cat_dict["TER-01"], Evidencia.Estado.APROBADA, "CIA714", "https://images.unsplash.com/photo-1577495508048-b635879837f1?auto=format&fit=crop&w=600&q=80"),
            ("Audiencia por ruidos molestos", "Mediación entre vecinos pasaje Los Aromos", items_g_objs[1], cat_dict["TER-01"], Evidencia.Estado.PENDIENTE, "CIA715", "https://images.unsplash.com/photo-1450133064473-71024230f91b?auto=format&fit=crop&w=600&q=80"),
            ("Operativo nocturno con Seguridad Ciudadana", "Ronda preventiva en sector Villa El Parque", items_g_objs[0], cat_dict["SEG-01"], Evidencia.Estado.PENDIENTE, "CIA716", "https://images.unsplash.com/photo-1508847154043-be5407fcaa5a?auto=format&fit=crop&w=600&q=80"),
            ("Reunión directiva JJVV San Bartolomé", "Planificación de actividades de Fiestas Patrias", items_g_objs[2], cat_dict["TER-01"], Evidencia.Estado.APROBADA, "CIA717", "https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=600&q=80"),
            ("Inspección letrero publicitario riesgoso", "Foto borrosa, no se aprecia numeración de poste", items_g_objs[0], cat_dict["INF-01"], Evidencia.Estado.RECHAZADA, "CIA718", "https://images.unsplash.com/photo-1520072959219-c595dc870360?auto=format&fit=crop&w=600&q=80"),
        ]

        for sol_tit, acc, it_med, cat, est_ev, cod_ev, url_img in actividades_carlos:
            act, created = Actividad.objects.get_or_create(
                funcionario=funcionarios_dict["carlos.terreno.cia"],
                actividad_solicitud=sol_tit,
                defaults={
                    "delegacion": dels["CIA"],
                    "item_medicion": it_med,
                    "catalogo_servicio": cat,
                    "accion_ejecutada": acc,
                    "contacto_nombre": "Vecino Anonimizado CIA",
                    "contacto_telefono": "+56987654321",
                    "latitud": -29.8950,
                    "longitud": -71.2500,
                    "fecha_actividad": datetime.date(2026, 8, 28)
                }
            )
            if not hasattr(act, 'evidencia'):
                obs = "Fotografía no nítida. Favor tomar foto desde ángulo frontal." if est_ev == Evidencia.Estado.RECHAZADA else ("Aprobado conforme en terreno." if est_ev == Evidencia.Estado.APROBADA else "")
                verif = delegados_dict["CIA"] if est_ev in [Evidencia.Estado.APROBADA, Evidencia.Estado.RECHAZADA] else None
                f_val = timezone.now() if verif else None
                Evidencia.objects.create(
                    actividad=act,
                    codigo_verificador=cod_ev,
                    url_foto_simulada=url_img,
                    estado=est_ev,
                    verificador=verif,
                    fecha_validacion=f_val,
                    observacion=obs
                )

        # 9. Casos Sociales con secuencia de 3 atenciones (RF-015, CA-04)
        caso1, _ = CasoSocial.objects.get_or_create(
            codigo_caso="CASO-CIA-2026-001",
            defaults={
                "persona_anonimizada": "Usuaria Adulto Mayor Sector El Sauce",
                "delegacion": dels["CIA"],
                "fecha_apertura": datetime.date(2026, 8, 10),
                "cerrado": False
            }
        )
        AtencionSocial.objects.get_or_create(
            caso=caso1,
            etapa=1,
            defaults={
                "tipo_atencion": "Diagnóstico y Postulación RSH",
                "detalle": "Se levanta ficha preliminar con situación de vulnerabilidad habitacional",
                "resultado": "Ficha aprobada en sistema nacional",
                "funcionario": funcionarios_dict["ana.social.cia"]
            }
        )
        AtencionSocial.objects.get_or_create(
            caso=caso1,
            etapa=2,
            defaults={
                "tipo_atencion": "Visita Domiciliaria de Verificación",
                "detalle": "Constatación en terreno de requerimiento de material de techumbre",
                "resultado": "Informe social derivado a DIDECO central",
                "funcionario": funcionarios_dict["ana.social.cia"]
            }
        )
        AtencionSocial.objects.get_or_create(
            caso=caso1,
            etapa=3,
            defaults={
                "tipo_atencion": "Entrega de Materiales y Cierre de Ayuda",
                "detalle": "Entrega de planchas de zinc y subsidio complementario de alimentos",
                "resultado": "Caso atendido satisfactoriamente",
                "funcionario": funcionarios_dict["ana.social.cia"]
            }
        )

        self.stdout.write(self.style.SUCCESS("Poblado de datos SGR completado con éxito!"))
