"""Ementas reais da Câmara do Rio e da ALERJ e a categoria que cada uma deve receber.

    cd pipeline && python -m unittest
"""
import unittest

from observatorio.classificar import classificar, simbolica

CASOS = [
    ("Dá o nome de Dr. Cleomar Paredes (1927-2025) a um logradouro no Município.", "logradouro"),
    ("Dá o nome de Preta Gil (1974-2025) a um equipamento cultural do Município do Rio de Janeiro.", "logradouro"),
    ("Dá o nome de Pastor Antônio Gilberto da Silva a uma escola da rede municipal de ensino público.", "logradouro"),
    ("Inclui o Dia Municipal do Tutor de Animais de Estimação no Calendário Oficial da Cidade consolidado "
     "pela Lei nº 5.146/2010.", "calendario"),
    ("INCLUI NO CALENDÁRIO OFICIAL DO ESTADO DO RIO DE JANEIRO O DIA ESTADUAL DE COMBATE AO RACISMO AMBIENTAL",
     "calendario"),
    ("Inclui na Lei nº 5.242/2011 o Instituto Cultural Zé Pretinho como de utilidade pública.", "utilidade_publica"),
    ("Inclui no Guia Oficial e no Roteiro Turístico e Cultural do Município o Restaurante Bosque da Praça, "
     "localizado no bairro da Praça Seca.", "patrimonio"),
    ("Declara como patrimônio histórico e cultural de natureza imaterial da Cidade do Rio de Janeiro a Bossa Nova.",
     "patrimonio"),
    ("Inclui a Rua Avaré como Polo Gastronômico e Cultural da Cidade na Lei nº 7.498/2022.", "patrimonio"),
    ("Considera de interesse cultural, social e turístico para o Município o evento Samba do Cardosão.", "patrimonio"),
    ("Inclui na Lei nº 5.919/2015 a Cidade de Évora, em Portugal, como cidade-irmã da Cidade do Rio de Janeiro.",
     "honraria"),
    ("Concede o título de Cidadão Honorário do Município do Rio de Janeiro a Pedro António dos Santos.", "honraria"),
    ("Institui o plano municipal de arborização das favelas do Rio de Janeiro, estabelece critérios de "
     "participação popular e dá outras providências.", "normativa"),
    ("Institui a Campanha Municipal de Combate ao Trabalho Infantil e de Busca Ativa Escolar no Município.",
     "normativa"),
    ("Susta os efeitos do Decreto Rio nº 55.000, de 2024.", "normativa"),
    ("Declara como Área de Especial Interesse Social a comunidade do Morro do Banco.", "normativa"),
    ("Reconhece como de interesse público o evento Rio Innovation Week.", "patrimonio"),
    ("DECLARA O LOTEAMENTO LOCALIZADO NO BAIRRO MANGUARIBA II COMO ÁREA DE INTERESSE SOCIAL, PARA FINS DE "
     "URBANIZAÇÃO E REGULARIZAÇÃO FUNDIÁRIA", "normativa"),
]


class TestClassificar(unittest.TestCase):
    def test_ementas_reais(self):
        for ementa, esperada in CASOS:
            with self.subTest(ementa=ementa[:60]):
                self.assertEqual(classificar(ementa), esperada)

    def test_lista_da_camara_prevalece(self):
        # a lista temática da Câmara vale mesmo quando a ementa não deixa claro
        self.assertEqual(classificar("Altera a Lei nº 1.234/2000.", tema_camara="logradouro"), "logradouro")

    def test_simbolica(self):
        self.assertTrue(simbolica("calendario"))
        self.assertFalse(simbolica("normativa"))


if __name__ == "__main__":
    unittest.main()
