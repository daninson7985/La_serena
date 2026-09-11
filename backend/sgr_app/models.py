import secrets
import string
import hashlib
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError


def generar_codigo_evidencia(prefijo="SGR"):
    chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
    aleatorio = ''.join(secrets.choice(chars) for _ in range(6))
    return f"{prefijo}{aleatorio}"


class Delegacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, unique=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Delegación"
        verbose_name_plural = "Delegaciones"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Cargo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        COORDINADOR = 'COORDINADOR', 'Coordinador Comunal'
        DELEGADO = 'DELEGADO', 'Delegado Municipal'
        FUNCIONARIO = 'FUNCIONARIO', 'Funcionario de Terreno'

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.FUNCIONARIO)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    delegacion = models.ForeignKey(Delegacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    telefono = models.CharField(max_length=30, blank=True, null=True)
    rut_anonimizado = models.CharField(max_length=20, blank=True, null=True)
    totp_secret = models.CharField(max_length=64, blank=True, null=True, help_text="Preparado para 2FA")
    requires_2fa = models.BooleanField(default=False)
    is_2fa_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.get_full_name() or self.username} [{self.get_rol_display()}]"


class PeriodoMedicion(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Ej: Trimestre 3 - 2026")
    fecha_inicio = models.DateField()
    fecha_termino = models.DateField()
    dias_computables = models.IntegerField(default=90)
    cerrado = models.BooleanField(default=False)
    umbral_colectivo = models.FloatField(default=80.0, help_text="Umbral mínimo colectivo (%)")
    tope_cumplimiento = models.FloatField(default=150.0, help_text="Tope máximo de cumplimiento (%)")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Período de Medición"
        verbose_name_plural = "Períodos de Medición"
        ordering = ['-fecha_inicio']

    def clean(self):
        if self.fecha_termino and self.fecha_inicio and self.fecha_termino < self.fecha_inicio:
            raise ValidationError("La fecha de término no puede ser anterior a la fecha de inicio.")

    def save(self, *args, **kwargs):
        if self.fecha_inicio and self.fecha_termino:
            self.dias_computables = max((self.fecha_termino - self.fecha_inicio).days + 1, 1)
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        estado = "Cerrado" if self.cerrado else "Activo"
        return f"{self.nombre} ({estado})"


class CatalogoServicio(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=150)
    area = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Catálogo de Servicio"
        verbose_name_plural = "Catálogo de Servicios"

    def __str__(self):
        return f"[{self.codigo}] {self.nombre}"


class ItemMedicion(models.Model):
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name='items_medicion')
    periodo = models.ForeignKey(PeriodoMedicion, on_delete=models.CASCADE, related_name='items_medicion')
    nombre_item = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    meta_cuantitativa = models.FloatField(default=1.0, help_text="Meta esperada en el período (>0)")
    ponderador = models.FloatField(default=25.0, help_text="Porcentaje de peso ponderado (0 a 100)")
    unidad_medida = models.CharField(max_length=50, default="Actividades")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Ítem de Medición"
        verbose_name_plural = "Ítems de Medición"
        unique_together = ('cargo', 'periodo', 'nombre_item')

    def clean(self):
        if self.meta_cuantitativa <= 0:
            raise ValidationError("La meta del ítem debe ser estrictamente mayor que cero.")
        if not (0 <= self.ponderador <= 100):
            raise ValidationError("El ponderador debe estar entre 0% y 100%.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre_item} ({self.cargo.nombre} - {self.ponderador}%)"


class CompromisoAgenda(models.Model):
    class Estado(models.TextChoices):
        INGRESADO = 'INGRESADO', 'Ingresado'
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        EN_PROCESO = 'EN_PROCESO', 'En Proceso'
        REALIZADO = 'REALIZADO', 'Realizado'

    solicitante = models.CharField(max_length=150, help_text="Nombre anonimizado de vecino u organización")
    delegacion = models.ForeignKey(Delegacion, on_delete=models.CASCADE, related_name='compromisos')
    responsable = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='compromisos_asignados')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_comprometida = models.DateField()
    area_apoyo = models.CharField(max_length=100, blank=True, null=True, help_text="Área interna de apoyo")
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.EN_PROCESO)
    observaciones = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='compromisos_creados')
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Compromiso de Agenda"
        verbose_name_plural = "Compromisos de Agenda"
        ordering = ['fecha_comprometida']

    def __str__(self):
        return f"[{self.estado}] {self.solicitante} - {self.delegacion.codigo} ({self.fecha_comprometida})"


class Actividad(models.Model):
    fecha_registro = models.DateTimeField(auto_now_add=True, help_text="Fecha y hora generada por el servidor")
    fecha_actividad = models.DateField(default=timezone.localdate, help_text="Fecha de realización")
    funcionario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='actividades')
    delegacion = models.ForeignKey(Delegacion, on_delete=models.CASCADE, related_name='actividades')
    item_medicion = models.ForeignKey(ItemMedicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='actividades')
    catalogo_servicio = models.ForeignKey(CatalogoServicio, on_delete=models.SET_NULL, null=True, blank=True, related_name='actividades')
    
    actividad_solicitud = models.CharField(max_length=255, help_text="Problema atendido o solicitud")
    accion_ejecutada = models.TextField(help_text="Acción desarrollada")
    contacto_nombre = models.CharField(max_length=150, blank=True, null=True, help_text="Nombre de referencia anonimizado")
    contacto_telefono = models.CharField(max_length=50, blank=True, null=True, help_text="Teléfono anonimizado")
    
    latitud = models.FloatField(blank=True, null=True)
    longitud = models.FloatField(blank=True, null=True)
    
    compromiso_agenda = models.ForeignKey(CompromisoAgenda, on_delete=models.SET_NULL, null=True, blank=True, related_name='actividades_derivadas')
    
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"Actividad #{self.id} - {self.funcionario.username} ({self.fecha_actividad})"


class Evidencia(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de Validación'
        APROBADA = 'APROBADA', 'Aprobada'
        RECHAZADA = 'RECHAZADA', 'Rechazada'
        CORRECCION = 'CORRECCION', 'Requiere Corrección'

    actividad = models.OneToOneField(Actividad, on_delete=models.CASCADE, related_name='evidencia')
    codigo_verificador = models.CharField(max_length=30, unique=True, editable=False, db_index=True)
    archivo_foto = models.ImageField(upload_to='evidencias/%Y/%m/', blank=True, null=True)
    url_foto_simulada = models.URLField(max_length=500, blank=True, null=True)
    hash_sha256 = models.CharField(max_length=64, blank=True, null=True)
    
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    verificador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='evidencias_validadas')
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    observacion = models.TextField(blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evidencia Fotográfica"
        verbose_name_plural = "Evidencias Fotográficas"

    @property
    def get_foto_url(self):
        if self.archivo_foto:
            try:
                return self.archivo_foto.url
            except Exception:
                pass
        return self.url_foto_simulada or 'https://images.unsplash.com/photo-1541888946425-d0fbb1861564?auto=format&fit=crop&w=600&q=80'

    def save(self, *args, **kwargs):
        if not self.codigo_verificador:
            prefijo = self.actividad.delegacion.codigo if self.actividad and self.actividad.delegacion else "SGR"
            self.codigo_verificador = generar_codigo_evidencia(prefijo)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Evidencia [{self.codigo_verificador}] - {self.estado}"


class CasoSocial(models.Model):
    codigo_caso = models.CharField(max_length=30, unique=True)
    persona_anonimizada = models.CharField(max_length=150)
    delegacion = models.ForeignKey(Delegacion, on_delete=models.CASCADE, related_name='casos_sociales')
    fecha_apertura = models.DateField(default=timezone.localdate)
    cerrado = models.BooleanField(default=False)

    def __str__(self):
        return f"Caso Social {self.codigo_caso} - {self.persona_anonimizada}"


class AtencionSocial(models.Model):
    ETAPAS = (
        (1, 'Primera Gestión / Diagnóstico'),
        (2, 'Segunda Gestión / Seguimiento'),
        (3, 'Tercera Gestión / Cierre o Derivación'),
    )
    caso = models.ForeignKey(CasoSocial, on_delete=models.CASCADE, related_name='atenciones')
    etapa = models.PositiveSmallIntegerField(choices=ETAPAS)
    fecha = models.DateField(default=timezone.localdate)
    tipo_atencion = models.CharField(max_length=100)
    detalle = models.TextField()
    resultado = models.CharField(max_length=150)
    funcionario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('caso', 'etapa')
        ordering = ['caso', 'etapa']

    def __str__(self):
        return f"{self.caso.codigo_caso} - Etapa {self.etapa}"


class RegistroAuditoria(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=50)
    entidad = models.CharField(max_length=50)
    identificador_registro = models.CharField(max_length=50)
    valor_anterior = models.JSONField(null=True, blank=True)
    valor_nuevo = models.JSONField(null=True, blank=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering = ['-fecha']

    def __str__(self):
        usr = self.usuario.username if self.usuario else "Sistema"
        return f"[{self.fecha.strftime('%Y-%m-%d %H:%M')}] {usr} -> {self.accion} {self.entidad} #{self.identificador_registro}"
