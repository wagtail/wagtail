from unittest import TestCase
import unittest
from unittest.mock import mock_open, patch
from wagtail.images.checks import has_jpeg_support
from wagtail.images import get_image_model

from .utils import Image, get_test_image_file, get_test_image_file_jpeg

import pytest # type: ignore

Image = get_image_model()
@pytest.mark.django_db

class TestHasJpegSupport(TestCase):
    def setUp(self):
        # cria uma imagem toda vez que é irá rodar um novo teste
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(filename="test.jpg"),
        )

    def tearDown(self):
        #para garatir que todos os mocks sejam limpos antes da execução de um novo teste
        patch.stopall()

    def _setup_mocks(self, mock_file_open, mock_image_open):
        #simula a abertura do arquivo
        mock_file_open.return_value = get_test_image_file_jpeg()

        #simula a abertura da imagem
        mock_image_open.return_value = get_test_image_file_jpeg()

### Case de Teste 1

    @patch('willow.image.Image.open')
    @patch('builtins.open', new_callable=mock_open, read_data=b'\xff\xd8\xff')
    def test_has_jpeg_support_success_read_ok_open_image_ok(self, mock_file_open, mock_image_open):
        self._setup_mocks(mock_file_open, mock_image_open)

        #chama a função a ser testada
        result = has_jpeg_support()

        #analisa se o suporte para o arquivo jpg/jpeg realmente foi verificado como o esperado
        self.assertTrue(result)

        #verifica se mock_file_open foi chamado
        mock_file_open.assert_called_once()

        #verifica se mock_image_open foi chamado
        mock_image_open.assert_called_once()

### Case de Teste 2

    @patch('willow.image.Image.open')
    @patch('builtins.open', new_callable=mock_open, read_data=b'\xff\xd8\xff')
    def test_has_jpeg_support_fail_read_ok_open_image_fail(self, mock_image_open, mock_file_open):
        self._setup_mocks(mock_file_open, mock_image_open)
        #simula Image(open) lançando uma exceção
        mock_image_open.side_effect = OSError("error opening the image")

        with self.assertRaises(OSError):

            result = has_jpeg_support()
            
            #verifica se a abertura do arquivo falhou como esperado
            self.assertFalse(result)
            

        #verifica se mock_image_open foi chamado 
        mock_image_open.assert_called_once()

### Case de Teste 3

    @patch('builtins.open', new_callable=mock_open, read_data=b'\xff\xd8\xff')
    @patch('willow.image.Image.open')
    def test_has_jpeg_support_fail_read_fail_open_image_ok(self, mock_image_open, mock_file_open):
        self._setup_mocks(mock_file_open, mock_image_open)

        mock_file_open.side_effect = OSError("error opening the file")

        with self.assertRaises(OSError): #verifica se o lançamento de uma exceção foi capturada
            
            result = has_jpeg_support()
            
            #verifica se a abertura do arquivo falhou como esperado
            self.assertFalse(result)


        mock_file_open.assert_called_once()
        mock_image_open.assert_not_called() #verifica se o mock_image_open não foi chamado já deu erro na abertura do arquivo

    

if __name__ == '__main__':
    unittest.main()