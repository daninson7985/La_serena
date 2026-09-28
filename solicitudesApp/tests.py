from django.test import TestCase
from django.urls import reverse


class SolicitudListadoTests(TestCase):
	def test_lista_muestra_controles_y_datos(self):
		response = self.client.get(reverse('solicitudes'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Agregar')
		self.assertContains(response, 'Modificar')
		self.assertContains(response, 'Eliminar')
		self.assertContains(response, 'Buscar')
		self.assertContains(response, 'Solicitud de luminaria defectuosa')

	def test_busqueda_filtra_solicitudes(self):
		response = self.client.get(reverse('solicitudes'), {'q': 'Centro'})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Solicitud de luminaria defectuosa')
		self.assertNotContains(response, 'Revisión de bache en avenida principal')
