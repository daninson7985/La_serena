from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from sgr_app.models import (
    Usuario, Delegacion, Cargo, Area, PeriodoMedicion, CatalogoServicio,
    ItemMedicion, Meta, Indicador, CompromisoAgenda, Actividad, Evidencia,
    CasoSocial, AtencionSocial, RegistroAuditoria, AjusteIncentivo
)

@admin.action(description="Desactivar seleccionados (Baja Lógica / Soft Delete)")
def desactivar_seleccionados(modeladmin, request, queryset):
    for obj in queryset:
        if hasattr(obj, 'desactivarUsuario'):
            obj.desactivarUsuario()
        elif hasattr(obj, 'desactivar_delegacion'):
            obj.desactivar_delegacion()
        elif hasattr(obj, 'desactivarArea'):
            obj.desactivarArea()
        elif hasattr(obj, 'desactivarCargo'):
            obj.desactivarCargo()
        elif hasattr(obj, 'desactivarItem'):
            obj.desactivarItem()
        elif hasattr(obj, 'activo'):
            obj.activo = False
            obj.save(update_fields=['activo'])
        elif hasattr(obj, 'estado'):
            obj.estado = False
            obj.save(update_fields=['estado'])
        elif hasattr(obj, 'is_active'):
            obj.is_active = False
            obj.save(update_fields=['is_active'])

@admin.action(description="Activar seleccionados")
def activar_seleccionados(modeladmin, request, queryset):
    for obj in queryset:
        if hasattr(obj, 'activarUsuario'):
            obj.activarUsuario()
        elif hasattr(obj, 'activar_delegacion'):
            obj.activar_delegacion()
        elif hasattr(obj, 'activarArea'):
            obj.activarArea()
        elif hasattr(obj, 'activarCargo'):
            obj.activarCargo()
        elif hasattr(obj, 'activarItem'):
            obj.activarItem()
        elif hasattr(obj, 'activo'):
            obj.activo = True
            obj.save(update_fields=['activo'])
        elif hasattr(obj, 'estado'):
            obj.estado = True
            obj.save(update_fields=['estado'])
        elif hasattr(obj, 'is_active'):
            obj.is_active = True
            obj.save(update_fields=['is_active'])

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'rol', 'cargo', 'delegacion', 'is_staff', 'is_active')
    list_filter = ('rol', 'delegacion', 'is_staff', 'is_active')
    actions = [desactivar_seleccionados, activar_seleccionados]
    fieldsets = UserAdmin.fieldsets + (
        ('Información Municipal SGR', {
            'fields': ('rol', 'cargo', 'delegacion', 'telefono', 'requires_2fa', 'is_2fa_verified')
        }),
    )

@admin.register(Delegacion)
class DelegacionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'ambito', 'telefono', 'email', 'activo')
    list_filter = ('ambito', 'activo')
    search_fields = ('nombre', 'codigo')
    actions = [desactivar_seleccionados, activar_seleccionados]

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'estado')
    list_filter = ('estado',)
    search_fields = ('nombre',)
    actions = [desactivar_seleccionados, activar_seleccionados]

@admin.register(PeriodoMedicion)
class PeriodoMedicionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_termino', 'dias_computables', 'cerrado', 'umbral_verde', 'umbral_ambar', 'tope_cumplimiento')
    list_editable = ('cerrado', 'umbral_verde', 'umbral_ambar', 'tope_cumplimiento')
    list_filter = ('cerrado',)
    search_fields = ('nombre',)

@admin.register(ItemMedicion)
class ItemMedicionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_item', 'cargo', 'periodo', 'ponderador', 'meta_cuantitativa', 'tipo_unidad', 'activo')
    list_editable = ('ponderador', 'meta_cuantitativa', 'activo')
    list_filter = ('periodo', 'cargo', 'tipo_unidad', 'activo')
    search_fields = ('nombre_item',)
    actions = [desactivar_seleccionados, activar_seleccionados]

@admin.register(Meta)
class MetaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'funcionario', 'item', 'periodo', 'valor_meta', 'ponderador', 'vigencia')
    list_editable = ('valor_meta', 'ponderador', 'vigencia')
    list_filter = ('periodo', 'vigencia', 'funcionario__delegacion')
    search_fields = ('nombre', 'funcionario__username', 'funcionario__first_name', 'funcionario__last_name')

@admin.register(Indicador)
class IndicadorAdmin(admin.ModelAdmin):
    list_display = ('meta', 'avance', 'cumplimiento', 'ponderacion', 'semaforo', 'fecha_calculo')
    list_filter = ('semaforo', 'fecha_calculo')
    search_fields = ('meta__nombre', 'meta__funcionario__username')

@admin.register(CompromisoAgenda)
class CompromisoAgendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'solicitante', 'delegacion', 'responsable', 'fecha_comprometida', 'area_apoyo', 'estado', 'creado_por')
    list_editable = ('estado',)
    list_filter = ('estado', 'delegacion', 'area_apoyo')
    search_fields = ('solicitante', 'descripcion', 'responsable__username')
    date_hierarchy = 'fecha_comprometida'

@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_actividad', 'solicitud_problema', 'funcionario', 'delegacion', 'item_medicion')
    list_filter = ('delegacion', 'fecha_actividad', 'item_medicion')
    search_fields = ('solicitud_problema', 'accion', 'funcionario__username', 'direccion')
    date_hierarchy = 'fecha_actividad'

@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ('codigo_verificador', 'actividad', 'estado', 'verificador', 'fecha_subida', 'fecha_validacion')
    list_editable = ('estado',)
    list_filter = ('estado', 'fecha_subida')
    search_fields = ('codigo_verificador', 'observacion')

@admin.register(CatalogoServicio)
class CatalogoServicioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'area', 'activo')
    list_filter = ('area', 'activo')
    search_fields = ('codigo', 'nombre')

@admin.register(CasoSocial)
class CasoSocialAdmin(admin.ModelAdmin):
    list_display = ('codigo_caso', 'persona_anonimizada', 'delegacion', 'fecha_apertura', 'cerrado')
    list_filter = ('delegacion', 'cerrado')
    search_fields = ('codigo_caso', 'persona_anonimizada')

@admin.register(AtencionSocial)
class AtencionSocialAdmin(admin.ModelAdmin):
    list_display = ('id', 'caso', 'etapa', 'tipo_atencion', 'fecha', 'funcionario')
    list_filter = ('tipo_atencion', 'etapa', 'fecha')
    search_fields = ('caso__codigo_caso', 'caso__persona_anonimizada')

@admin.register(AjusteIncentivo)
class AjusteIncentivoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'tipo', 'valor_porcentaje', 'estado', 'aprobadoPor', 'fecha_registro')
    list_editable = ('estado',)
    list_filter = ('tipo', 'estado')
    search_fields = ('funcionario__username', 'motivo')

@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'accion', 'entidad', 'identificador_registro', 'ip_origen')
    list_filter = ('accion', 'entidad', 'fecha')
    search_fields = ('usuario__username', 'accion', 'entidad', 'identificador_registro')
    readonly_fields = ('usuario', 'accion', 'entidad', 'identificador_registro', 'valor_anterior', 'valor_nuevo', 'ip_origen', 'fecha')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
