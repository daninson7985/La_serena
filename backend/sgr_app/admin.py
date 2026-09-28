from django.contrib import admin
from .models import Categoria, Requisito, Servicio


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
	list_display = ('nombre',)
	search_fields = ('nombre',)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'categoria', 'dias_habiles', 'costo')
	search_fields = ('nombre', 'categoria__nombre', 'descripcion')
	list_filter = ('categoria',)


@admin.register(Requisito)
class RequisitoAdmin(admin.ModelAdmin):
	list_display = ('descripcion', 'servicio')
	search_fields = ('descripcion', 'servicio__nombre')
	list_filter = ('servicio',)
