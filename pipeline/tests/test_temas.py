"""Ementas reais e o tema que cada uma deve receber.

    cd pipeline && python -m unittest
"""
import unittest

from observatorio.temas import TEMAS, tema

CASOS = [
    ("Dispõe sobre a adoção de Programa de Prevenção à Sepse (infecção generalizada) e de informações básicas, "
     "por hospitais, clínicas e unidades de saúde.", "saude"),
    ("Dispõe sobre as restrições ao fumo nas áreas onde estejam instaladas Academias da Terceira Idade - ATIS.",
     "saude"),
    ("Estabelece no Município do Rio de Janeiro a divulgação, em local visível, do cardápio semanal da merenda escolar.",
     "educacao"),
    ("Dispõe sobre a preferência de vagas para irmãos no mesmo estabelecimento de ensino público no Município.",
     "educacao"),
    ("Institui o Estatuto Municipal de Promoção da Igualdade Racial no âmbito do Município do Rio de Janeiro.",
     "direitos"),
    ("Cria o Programa Emergencial de Combate à Fome no âmbito do Município do Rio de Janeiro.", "direitos"),
    ("Dispõe sobre a implementação e operação do Sistema de Área Azul Digital no Município do Rio de Janeiro.",
     "transporte"),
    ("Dispõe sobre o uso de arma de fogo pela divisão de elite da GM-RIO – Força Municipal, órgão da Guarda "
     "Municipal do Rio de Janeiro.", "seguranca"),
    ("Cria a campanha permanente de conscientização acerca dos perigos da prática de soltura de pipa com linhas "
     "cortantes em vias públicas.", "seguranca"),
    ("Dispõe sobre o replantio de árvores caídas e retiradas no Município do Rio de Janeiro.", "ambiente"),
    ("Dispõe sobre os serviços de day care e hospedagem de animais domésticos no Município do Rio de Janeiro.",
     "ambiente"),
    ("Declara a localidade de Manguariba III, situada no Bairro de Paciência, como Área de Especial Interesse "
     "Social (AEIS), para fins de urbanização.", "urbanismo"),
    ("Dispõe sobre a proibição da comercialização e distribuição de produtos alimentícios cuja embalagem contenha "
     "grampos e similares.", "economia"),
    ("Institui o ambiente regulatório controlado (sandbox regulatório) no Município do Rio de Janeiro.", "economia"),
    ("Institui no Município do Rio de Janeiro o Programa Pequenos Atletas.", "cultura"),
    ("Estima a Receita e Fixa a Despesa do Município do Rio de Janeiro para o exercício financeiro de 2025.",
     "tributos"),
    ("Institui o Regime de Previdência Complementar dos ocupantes de cargos efetivos do Poder Executivo.",
     "administracao"),
    ("Altera a Lei Complementar nº 229, de 14 de julho de 2021.", "outros"),
]


class TestTemas(unittest.TestCase):
    def test_ementas_reais(self):
        for ementa, esperado in CASOS:
            with self.subTest(ementa=ementa[:60]):
                self.assertEqual(tema(ementa), esperado)

    def test_texto_da_lei_quando_a_ementa_so_remete(self):
        self.assertEqual(tema("Altera a Lei nº 3.167, de 2000.",
                              "Art. 1º Fica assegurada a matrícula do aluno na escola municipal mais próxima."),
                         "educacao")

    def test_todo_tema_tem_rotulo(self):
        self.assertIn("outros", TEMAS)
        for ementa, esperado in CASOS:
            self.assertIn(esperado, TEMAS)


if __name__ == "__main__":
    unittest.main()
