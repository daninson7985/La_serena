from rest_framework import serializers
from sgr_app.models import (
    Usuario, Delegacion, Cargo, PeriodoMedicion, CatalogoServicio,
    ItemMedicion, CompromisoAgenda, Actividad, Evidencia,
    CasoSocial, AtencionSocial, RegistroAuditoria
)


class DelegacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delegacion
        fields = '__all__'


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = '__all__'


class UsuarioSerializer(serializers.ModelSerializer):
    cargo_nombre = serializers.ReadOnlyField(source='cargo.nombre')
    delegacion_nombre = serializers.ReadOnlyField(source='delegacion.nombre')
    delegacion_codigo = serializers.ReadOnlyField(source='delegacion.codigo')

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'rol',
            'cargo', 'cargo_nombre', 'delegacion', 'delegacion_nombre', 'delegacion_codigo',
            'telefono', 'rut_anonimizado', 'requires_2fa', 'is_active'
        ]
        read_only_fields = ['id']


class PeriodoMedicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoMedicion
        fields = '__all__'


class CatalogoServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogoServicio
        fields = '__all__'


class ItemMedicionSerializer(serializers.ModelSerializer):
    cargo_nombre = serializers.ReadOnlyField(source='cargo.nombre')
    periodo_nombre = serializers.ReadOnlyField(source='periodo.nombre')

    class Meta:
        model = ItemMedicion
        fields = '__all__'


class EvidenciaSerializer(serializers.ModelSerializer):
    verificador_nombre = serializers.ReadOnlyField(source='verificador.get_full_name')

    class Meta:
        model = Evidencia
        fields = [
            'id', 'actividad', 'codigo_verificador', 'archivo_foto', 'url_foto_simulada',
            'hash_sha256', 'estado', 'verificador', 'verificador_nombre',
            'fecha_validacion', 'observacion', 'fecha_subida'
        ]
        read_only_fields = ['id', 'codigo_verificador', 'hash_sha256', 'fecha_subida']


class CompromisoAgendaSerializer(serializers.ModelSerializer):
    delegacion_nombre = serializers.ReadOnlyField(source='delegacion.nombre')
    delegacion_codigo = serializers.ReadOnlyField(source='delegacion.codigo')
    responsable_nombre = serializers.ReadOnlyField(source='responsable.get_full_name')

    class Meta:
        model = CompromisoAgenda
        fields = '__all__'


class ActividadSerializer(serializers.ModelSerializer):
    funcionario_nombre = serializers.ReadOnlyField(source='funcionario.get_full_name')
    delegacion_nombre = serializers.ReadOnlyField(source='delegacion.nombre')
    delegacion_codigo = serializers.ReadOnlyField(source='delegacion.codigo')
    item_nombre = serializers.ReadOnlyField(source='item_medicion.nombre_item')
    evidencia = EvidenciaSerializer(read_only=True)

    class Meta:
        model = Actividad
        fields = [
            'id', 'fecha_registro', 'fecha_actividad', 'funcionario', 'funcionario_nombre',
            'delegacion', 'delegacion_nombre', 'delegacion_codigo', 'item_medicion', 'item_nombre',
            'catalogo_servicio', 'actividad_solicitud', 'accion_ejecutada',
            'contacto_nombre', 'contacto_telefono', 'latitud', 'longitud',
            'compromiso_agenda', 'evidencia', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['id', 'fecha_registro', 'creado_en', 'actualizado_en']


class AtencionSocialSerializer(serializers.ModelSerializer):
    funcionario_nombre = serializers.ReadOnlyField(source='funcionario.get_full_name')

    class Meta:
        model = AtencionSocial
        fields = '__all__'


class CasoSocialSerializer(serializers.ModelSerializer):
    delegacion_nombre = serializers.ReadOnlyField(source='delegacion.nombre')
    atenciones = AtencionSocialSerializer(many=True, read_only=True)

    class Meta:
        model = CasoSocial
        fields = '__all__'


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.ReadOnlyField(source='usuario.get_full_name')

    class Meta:
        model = RegistroAuditoria
        fields = '__all__'
