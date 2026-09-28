from django.test import TestCase
from django.urls import reverse


class ServicioListadoTests(TestCase):
	def test_lista_muestra_controles_y_datos(self):
		response = self.client.get(reverse('servicios'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Agregar')
		self.assertContains(response, 'Modificar')
		self.assertContains(response, 'Eliminar')
		self.assertContains(response, 'Buscar')
		self.assertContains(response, 'Permisos de construcción')

	def test_busqueda_filtra_servicios(self):
		response = self.client.get(reverse('servicios'), {'q': 'Comercio'})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Patente Comercial')
		self.assertNotContains(response, 'Licencia de Conducir')
