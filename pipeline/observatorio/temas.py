"""Tema das leis e projetos que não são simbólicos (saúde, transporte, impostos...).

Cada tema tem uma lista de termos procurados na ementa (sem acento, minúsculas). Ganha o tema com
mais termos encontrados; no empate, o que aparece primeiro na ementa, que costuma ser o assunto
principal ("Dispõe sobre câmeras de segurança nas escolas" é segurança). Ementa que só remete a
outra lei ("Altera a Lei nº 5.146") não diz o assunto: aí vale o começo do texto da lei, quando há.
"""
from __future__ import annotations

import re

from .classificar import _normalizar

TEMAS = {
    "saude": "Saúde",
    "educacao": "Educação",
    "direitos": "Direitos e assistência social",
    "transporte": "Transporte e trânsito",
    "seguranca": "Segurança e defesa civil",
    "ambiente": "Meio ambiente e animais",
    "urbanismo": "Obras, moradia e urbanismo",
    "economia": "Comércio, trabalho e consumidor",
    "cultura": "Cultura, esporte e turismo",
    "tributos": "Impostos e orçamento",
    "administracao": "Governo e servidores",
    "outros": "Outros",
}

_TERMOS = {
    "saude": r"""saude|sus|hospita\w*|medic[oa]s?|medicament\w*|doencas?|doentes?|vacina\w*|imuniza\w*|
        clinicas?(?! veterinari)|upas?|cancer|oncolog\w*|diabet\w*|hiv|aids|hepatite\w*|tuberculose|
        doacao de (sangue|orgaos|medula|leite)|sangue|gestantes?|parto|pre-?natal|maternidades?|obstetr\w*|
        odontolog\w*|dentist\w*|saude bucal|psicolog\w*|psiquiatr\w*|terapias?|terapeutic\w*|fisioterap\w*|
        enfermag\w*|enfermeir\w*|obesidade|nutric\w*|dengue|zika|chikungunya|epidemi\w*|pandemi\w*|
        vigilancia sanitaria|exames?|diagnostic\w*|tratamentos?|pacientes?|ambulancias?|samu|
        farmac\w*|leitos?|teste do pezinho|amamenta\w*|aleitamento|mamografia|suicidio|fibromialgia|
        epilepsia|doencas? raras?|alzheimer|parkinson|lupus|esclerose|desfibrilador\w*|primeiros socorros|
        cirurgi\w*|transplante\w*|fumo|fumar|amianto|cegueira|oftalmolog\w*|retinopatia|tabag\w*|cigarr\w*|depressao|ansiedade|panico|
        saude mental|transtornos? mentais?|sindrome\w*|prontuario\w*|atencao (basica|primaria)|agentes? comunitarios? de saude""",
    "educacao": r"""educac\w*|educacional|educador\w*|escolas?|escolar\w*|ensino|alunos?|alunas?|estudant\w*|
        creches?|professor\w*|magisterio|pedagog\w*|merenda|sala de aula|alfabetiza\w*|vestibular|
        universidad\w*|faculdade\w*|bolsas? de estudo|pre-?vestibular|ano letivo|matricula\w*|
        curricul\w*|gremios? estudant\w*|tempo integral|extracurricular\w*|grade curricular|ciencias?|cientific\w*|rede municipal de ensino|educandos?|bullying""",
    "direitos": r"""mulher|mulheres|feminin\w*|genero|violencia (domestica|contra a mulher|obstetrica|sexual)|
        maria da penha|importunacao|abuso sexual|feminicid\w*|assedio|estupro|criancas?|adolescen\w*|infancia|juventude|idos[oa]s?|
        terceira idade|pessoas? (com|portadoras? de) deficiencia|pcd|deficien\w*|autis\w*|
        transtorno do espectro|tea|sindrome de down|tdah|surd[oa]s?|libras|ceg[oa]s?|braile|braille|
        mobilidade reduzida|acessib\w*|neurodivers\w*|neuroatipic\w*|atipic[oa]s?|lgbt\w*|transexua\w*|
        travesti\w*|homofobi\w*|transfobi\w*|nome social|racia\w*|racismo|negr[oa]s?|afro\w*|quilombo\w*|
        indigena\w*|intoleranc\w*|discrimina\w*|preconceito|igualdade|equidade|direitos humanos|cidadania|
        assistencia social|socioassistencia\w*|vulnerab\w*|situacao de rua|populacao de rua|fome|
        seguranca alimentar|banco de alimentos|restaurantes? populares?|cozinhas? comunitarias?|
        transferencia de renda|renda (minima|basica)|bolsa familia|cesta basica|pobreza|migrantes?|
        refugiad\w*|dependentes? quimicos?|egress[oa]s? do sistema prisional|conselhos? tutelar\w*|
        programas? sociais?|cuidador\w*|orfa[os]s?|acolhimento institucional|tutela""",
    "transporte": r"""transporte\w*|onibus|brt|vlt|metro|metroviari\w*|trens?|ferrovi\w*|barcas?|transito|
        mobilidade(?! reduzida)|bicicleta\w*|ciclovia\w*|ciclofaixa\w*|patinete\w*|taxis?|taxista\w*|
        mototaxi\w*|motofrete\w*|vans?|motoristas?|passageir[oa]s?|passagens?|bilhete unico|riocard|
        estacionamento\w*|estacionar|veicul\w*|automove\w*|motociclet\w*|motos?|carros?|pedestres?|
        semaforo\w*|radar\w*|guinchos?|reboque|detran|cet-?rio|pontos? de (onibus|parada)|
        abrigos? de onibus|garagem|garagens|area azul|pedagios?|linha amarela|transolimpica|frota\w*|condutor\w*|habilitacao|aplicativos? de transporte""",
    "seguranca": r"""seguranca publica|guarda municipal|policia\w*|policiais|violencia urbana|crimes?|
        criminal\w*|criminais|foragid\w*|inundac\w*|criminos\w*|delito\w*|assaltos?|roubos?|furtos?|armas?|armament\w*|desarmamento|
        videomonitoramento|cameras?|ordem publica|seop|controle urbano|milicia\w*|trafico|desaparecid\w*|
        balas? perdidas?|tiroteio\w*|defesa civil|bombeir\w*|desastres?|chuvas?|enchente\w*|alagament\w*|
        deslizament\w*|sirenes?|evacuacao|incendio\w*|vandalismo|pichac\w*|risco geologico|linhas? cortantes?|cerol|
        seguranca (nas|nos|das|dos|em) (escolas|unidades|eventos|predios)""",
    "ambiente": r"""meio ambiente|ambienta\w*|sustentab\w*|sustentave\w*|clima|climatic\w*|aquecimento global|
        carbono|emissoes|poluic\w*|poluente\w*|ruidos?|poluicao sonora|arvores?|arboriza\w*|florest\w*|
        reflorest\w*|mata atlantica|areas? verdes?|hortas?|agroecolog\w*|organicos?|agrotox\w*|lixo|
        residuos?|reciclag\w*|reciclave\w*|coleta seletiva|compostag\w*|plasticos?|descartave\w*|canudos?|
        sacolas?|isopor|energia (solar|renovave\w*|limpa)|fotovoltaic\w*|reuso de agua|agua de reuso|
        aproveitamento de agua|nascentes?|lagoas?|baia de guanabara|praias?|manguez\w*|restinga|fauna|flora|
        animal|animais|caes|cao|gatos?|pets?|castrac\w*|maus[- ]tratos|zoonose\w*|veterinari\w*|
        tracao animal|fogos de artificio|unidades? de conservacao|parque natural|recursos hidricos|
        desmatamento|queimada\w*|biodiversidade|abelhas?|passaros|aves|plantas?|plantio|agricultur\w*|agricultor\w*|hortifrut\w*""",
    "urbanismo": r"""urbanist\w*|urbanos?|urbanas?|zoneamento|uso do solo|ocupacao do solo|parcelamento do solo|
        loteament\w*|edifica\w*|construc\w*|obras?|imove(l|is)|habitac\w*|moradia\w*|minha casa|
        regularizacao fundiaria|titulacao|favelas?|areas? de especial interesse|aeis|peu|plano diretor|
        gabarito|afastamento|licenciamento|habite-se|codigo de obras|mais-valia|outorga onerosa|calcadas?|
        iluminacao publica|saneamento|esgot\w*|drenagem|pavimenta\w*|asfalt\w*|buracos?|mobiliario urbano|
        espacos? publicos?|vias? publicas?|cabos?|fiacao|postes?|antenas?|estacoes? radio ?base|
        infraestrutura|bairros?|planejamento urbano|retrofit|porto maravilha|reviver centro|fachadas?|
        demolic\w*|terrenos?|lotes?|condominio\w*|predios?|elevador\w*|marquises?|toldos?|agua potavel|
        abastecimento de agua|aguas pluviais|hidrometr\w*|fornecimento de agua|
        especial interesse social|urbaniza\w*|reurbaniza\w*|regulariza\w* fundiaria""",
    "economia": r"""consumidor\w*|procon|comercio|comercia\w*|ambulantes?|camelo\w*|feiras?|feirantes?|
        mercados?|supermercad\w*|shopping\w*|bares|restaurant\w*|lanchonete\w*|food ?trucks?|empresas?|
        empresari\w*|empreend\w*|microempre\w*|mei|startups?|inovac\w*|sandbox|tecnologi\w*|digita\w*|
        internet|wi-?fi|aplicativos?|empregos?|trabalh\w*|desemprego|qualificacao profissional|
        capacitacao profissional|jovem aprendiz|primeiro emprego|geracao de (emprego|renda)|
        economia (solidaria|criativa|circular)|economic\w*|cooperativas?|propagandas?|publicidade|anuncios?|
        letreiros?|outdoors?|horario de funcionamento|alvara\w*|licenca de funcionamento|precos?|
        taxa de servico|gorjeta|nota fiscal|bancari\w*|agencias? bancarias?|caixas? eletronicos?|
        licenca para localizacao|pesca|pescador\w*|concessionari\w*|faturas?|cobrancas?|filas?|plano de saude|planos de saude|cemiteri\w*|funerari\w*|estabelecimentos? (comerciais|empresariais|privados)|lojas?|varejo|
        fornecedor\w*|delivery|entregador\w*|ifood|uber""",
    "cultura": r"""cultur\w*|arte|artes|artist\w*|artesan\w*|musica\w*|musicos?|samba|funk|carnava\w*|
        blocos?|escolas? de samba|teatro\w*|cinemas?|audiovisua\w*|danca|capoeira|literatur\w*|livros?|
        leitura|bibliotecas?|museus?|exposic\w*|festiva\w*|festas?|eventos?|shows?|memoria|histori\w*|
        esport\w*|desport\w*|atletas?|futebol|jogos|olimpi\w*|paralimpi\w*|competic\w*|academias?|
        atividades? fisicas?|ginastica|lazer|recreac\w*|brincar|turism\w*|turist\w*|hote(l|is)|
        religios\w*|igrejas?|templos?|culto|terreiros?|gastronom\w*|grafite|arte urbana|praia de surf|surf""",
    "tributos": r"""tribut\w*|impostos?|iptu|iss|issqn|itbi|taxas?|isenc\w*|isent\w*|remissao|anistia|
        divida ativa|parcelamento de (debitos|dividas)|refis|orcament\w*|diretrizes orcamentarias|ldo|loa|
        plano plurianual|ppa|creditos? (adicion\w*|suplementar\w*|especia\w*)|receitas?|despesas?|
        financeir\w*|emprestimos?|operac(ao|oes) de credito|endividamento|fisca(l|is)|arrecada\w*|
        contribuicao de melhoria|cosip|preco publico|valor venal|planta de valores|beneficios? fiscais?|
        incentivos? fiscais?|dividas?|debitos?|tesouro""",
    "administracao": r"""servidor\w*|funcionalismo|cargos?|carreira\w*|quadro de pessoal|quadro permanente|
        plano de cargos|vencimentos?|remunerac\w*|salari\w*|gratificac\w*|subsidios?|piso salarial|abono\w*|
        previdenc\w*|previ-?rio|funprevi|aposentad\w*|pensao|pensoes|concursos? publicos?|estagi\w*|
        comissionad\w*|estrutura (administrativa|organizacional|basica)|reestrutura\w*|secretarias?|
        autarquia\w*|empresa publica|fundacao (municipal|publica)|orgaos?|administracao (publica|direta|indireta)|
        licitac\w*|contratos?|compras publicas|pregao|parcerias? publico-?privadas?|ppp|concessoes? de servic\w*|
        permissao de uso|cessao de uso|doacao de (imove(l|is)|bens?|area)|alienacao|desafeta\w*|
        transparencia|acesso a informacao|dados abertos|ouvidoria\w*|controladoria|corregedoria|
        procuradoria|tribunal de contas|camara municipal|vereador\w*|regimento interno|mesa diretora|
        processo legislativo|conselhos? municipa\w*|governo digital|desburocratiz\w*|processos? administrativos?|
        publicidade (oficial|institucional)|diario oficial|hino|bandeira|nepotismo|agentes? publicos?|
        lei organica|poder legislativo|prefeito|vice-prefeito|subprefeitura\w*|regiao administrativa|
        regioes administrativas|guarda-vidas""",
}

_REGRAS = {t: re.compile(r"\b(?:" + re.sub(r"\s*\n\s*", "", p) + r")\b") for t, p in _TERMOS.items()}

# ementas que só apontam para outra norma: o assunto está no texto
_REMISSIVA = re.compile(r"^(altera|acrescenta|inclui|modifica|revoga|da nova redacao|regulamenta)\b.{0,90}"
                        r"\b(lei|leis|decreto|lei complementar)\b[^,;]*$")


def _pontuar(texto: str) -> tuple[str | None, int]:
    melhor: tuple[int, int, str] | None = None
    for tema, regra in _REGRAS.items():
        achados = list(regra.finditer(texto))
        if not achados:
            continue
        chave = (len(achados), -achados[0].start(), tema)
        if melhor is None or chave[:2] > melhor[:2]:
            melhor = chave
    return (melhor[2], melhor[0]) if melhor else (None, 0)


def tema(ementa: str, texto: str | None = None) -> str:
    e = _normalizar(ementa)
    achado, n = _pontuar(e)
    if texto and (achado is None or (n == 1 and _REMISSIVA.search(e))):
        # o começo do texto (depois da ementa repetida) costuma dizer do que a lei trata
        t = _normalizar(texto)[:900]
        achado_texto, n_texto = _pontuar(t)
        if achado_texto and (n_texto >= 2 or achado is None):
            return achado_texto
    return achado or "outros"
