import os
import glob
import fnmatch
import json
import re
import traceback
import datetime

from modules.buffer import UserInput
from modules.tags import Tags

from utils.loading import *
from utils.logger import *
from utils.match import *

"""
1. ak som v proj root dir
2. solutions = get_solutions(proj dir)
3. if env.cwd.proj.solutions.getkeys() != solutions
4. nacitaj znovu solutions: env.cwd.proj.reload_solutions()
"""

class Solution:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.tags = None
        self.test_tags = None

        self.test_notes = {} # poznamky k automatickym testom
        self.user_notes = [] # dalsie nezavisle poznamky


    def add_user_note(self, text):
        self.user_notes.append(text)

    def add_test_note(self, version, text):
        if version in self.test_notes:
            self.test_notes[version].append(text)
        else:
            self.test_notes[verion] = [text]

    def get_test_notes_for_version(self, version):
        if version in self.test_notes:
            return self.test_notes[version]
        return []


class Project:
    def __init__(self, path):
        self.path = path
        self.name = ""
        self.created = None
        self.solution_id = None
        self.max_score = 0

        self.sut_required = ""
        self.sut_ext_variants = []
        self.solution_info = []
        self.tests_info = []

        self.description = ""
        self.test_timeout = 0

        self.solutions = None

    def reload_solutions(self):
        self.solutions = self.load_solutions()

    def load_solutions(self):
        res = {}
        # get solution dirs
        dirs = set()
        items = os.listdir(self.path) # list all dirs and files in proj dir
        for item in items:
            path = os.path.join(self.path, item)
            if os.path.isdir(path) and bool(re.match(self.solution_id, item)):
                dirs.add(path)
        solutions = list(dirs)

        for solution_dir in solutions:
            solution_id = os.path.basename(solution_dir)
            solution_data = Solution(solution_dir)

            # load solution tags
            solution_data.tags = load_solution_tags(solution_dir)
            solution_data.test_tags = load_tests_tags(os.path.join(solution_dir, TESTS_DIR))

            # load solution reports
            # TODO


            res[solution_id] = solution_data
        return res

    def get_solution_dirs(self):
        res = []
        if self.solutions:
            for name, data in self.solutions.items():
                res.append(data.path)
        return res

    def set_values_from_conf(self, data):
        try:
            self.name = data['name']
            self.created = data['created']
            self.solution_id = data['solution_id']
            self.max_score = data['max_score']
            self.sut_required = data['sut_required']
            self.sut_ext_variants = data['sut_ext_variants']
            self.solution_info = data['solution_info']
            self.tests_info = data['tests_info']
            self.solutions = self.load_solutions()
            return True
        except:
            log("wrong data for proj")
            return False


    def set_default_values(self):
        self.name = "project"
        self.created = datetime.date.today() # date of creation
        self.solution_id =  "x[a-z]{5}[0-9]{2}" # default solution identifier: xlogin00
        self.max_score = 10

        self.sut_required = "sut" # default file name of project solution is "sut" (system under test)
        self.sut_ext_variants = ["*sut*", "sut.sh", "sut.bash"]
        self.solution_info = self.get_solution_info()
        self.tests_info = self.get_tests_info()
        self.solutions = self.load_solutions()

        self.test_timeout = 5


    def to_dict(self):
        return {
            'name': self.name,
            'created': self.created,
            'solution_id': self.solution_id,
            'max_score' : self.max_score,
            'sut_required': self.sut_required,
            'sut_ext_variants': self.sut_ext_variants,
            'solution_info': self.solution_info,
            'tests_info': self.tests_info
        }
        #     'test_timeout': self.test_timeout


    """
    solution info = informacie ktore sa zobrazia pre xlogin00 dir
    * informacie sa zarovnaju vpravo
    * informacie su oddelene medzerou
    * ak informacia nematchne ani jeden predikat -- nema sa zobrazit, zostane namiesto nej prazdne miesto

    * identifier = id informacie (int)
                -- urcuje poradie v akom sa informacie zobrazuju zprava
                -- ak sa do okna nezmestia vsetky info, ako prve sa schovaju tie s najvacsim identifier
    * visualization = ako sa ma informacia zobrazit
                -- idealne pouzit len jeden znak
                -- cim menej miesta to zaberie, tym viac roznych info viem zobrazit
                -- mozno pouzit aj priamo hodnotu parametra nejakeho tagu --- POZOR !!!
                    -- mozu sa pouzivat len hodnoty z jedno-parametrovych tagov
                    -- musi byt dodrzany striktny format zadavania: tag_name.param_idx kde param_idx je cislo > 0
                    -- napr: last_testing.1 alebo scoring.2
                    -- zobrazenie hodnoty mozu byt rozne pre kazde riesenie
                        -- to moze viest k tomu ze sa zobrazovane informacie rozsynchronizuju
                        -- vizualne to teda nemusi vyzerat dobre (ked sa ostatne info posunu lebo je tento parameter dlhy)
                        -- odporuca sa preto definovat hodnotu length (vid dalej)
    * length = (optional) urcuje maximalnu dlzku informacie pre vizualizaciu
                -- tato hodnota nemusi byt definovana
                -- je vhodne definovat ak sa pri vizualizacii pouziva parameter tagu (hodnota ktora moze byt premenna pre rozne riesenia)
                -- napr. ak viem ze vizualizujem celkove skore riesenia
                    -- viem ze nebude viac ako 100, teda viem ze bude max dvojciferne
                    -- chcem ho teda zarovnat na dva znaky --> length=2
                    -- ak pre dane riesenie nenajdem #scoring tak bude namiesto cisla zobrazena medzera o velkosti 2
    * description = strucny popis informacie
                -- lubovolny retazec (idealne nie moc dlhy)
                -- zobrazi sa v nahlade informacii (po zadani "show details about project solution informations" v menu)
    * predicates = zoznam predikatov vo forme predikat + farba
                -- urcuju za akych podniemok sa informacia zobrazi a s akou farbou
                -- na zobrazenie informacie sa musi aspon jedna podniemka z predikatov [...] vyhodnotit ako True
                -- ak su splnene viacere podmienky predikatov, pouzije sa farba z prveho, ktory sa matchne
                * predicate = podmienka zobrazenia informacie
                        -- pracuje s tagmi pripadne s ich parametrami
                        -- u tagov sa skuma:
                            -- existencia   (funguje rovnako ako filter podla tagov)
                                            = odkazuje na vsoebecnu existenciu tagu bez ohladu na parameter,  napr: plag
                                            = odkazuje na zhodu tagu aj parametru podla regex,                napr: scoring(^[0-5])
                            -- porovnanie = odkazuje na porovnanie tagu s niecim,                             napr: scoring.1 > 0
                * color = farba zobrazenia informacie
                        -- ak sa podmienka v danom predikate vyhodnoti na True
                        -- potom sa pouzije tato definovana farba na vyzobrazenie informacie
                        -- ak farba nie je definovana, pouzije sa Normal (biela)
                        -- farba sa zadava pomocou
                                ??? preddefinovanych hodnot: normal, red, green, blue  (cyan, yellow, orange, pink)
                                ??? GRB hodnot
                                ??? #hex hodnot
    -- tagy mozno pouzit u visualization a predicate
    -- ak ma nejake info rovnaky indentifier, porovnaju sa jeho predikaty... --> idealne sa tomuto vyhnut !!!
        -- mozu s tym byt problemy ked je rozne dlha vizualizacia informacii s rovnakym identifikatorom
            -- ak je splneny predikat niektorej z info  --> zobrazi sa info ktora sa prva matchne
            -- ak nie je splneny predikat ziadnej       --> zobrazi sa prazdne miesto poslednej nematchnutej (jej length)
            -- ak je splneny predikat viacerych         --> zobrazi sa info ktora je prva v poradi v zozname (prva ktora matchne)


    POSTUP PRI ZOBRAZOVANI:
    1. get solution_info from proj conf
    2. zoradir solution_info podla identifier (od najmensieho po najvacsie)
    3. for info in solution_info -- citam zprava a pridavam zlava
    a) if visualization je hodnota parametru tagu
        1. zisti tuto hodnotu
        2. ak taky tag neexistuje --> nezobrazuj info a chod dalej
        3. pozri ci je definovana length
        4. ak neni, by default daj length = 1 medzera
    b) else
        1. pozri ci je definovana length
        2. ak neni, by default daj length = len(visualization)
    c) for predicate in predicates -- resp while predicate not matches
        1. spracuj predicate
        2. vyhodnot predicate
        3. ak matchol, konci a vrat farbu ak je definovana, inak vrat Normal farbu
        4. ak nematchol pokracuj v cykle
        5. ak uz nie su dalsie predicates --> nezobrazuj info a chod dalej
    d) ak mas co zobrazit, pridaj zlava hodnotu v danej farbe + 1 medzeru
    e) ak nemas co zobrazit, pridaj zlava medzeru*length + 1 medzeru

    """

    def get_only_valid_solution_info(self):
        result = []
        required_keys = ["identifier", "visualization", "predicates"]
        supported_keys = required_keys.copy()
        supported_keys.extend(["length", "description"])
        for info in self.solution_info:
            info_keys = list(info.keys())
            all_required_in = all(required in info_keys for required in required_keys)
            all_keys_supported = all(info in supported_keys for info in info_keys)
            if all_required_in and all_keys_supported:
                result.append(info)
        return result

    def get_only_valid_tests_info(self):
        result = []
        required_keys = ["identifier", "visualization", "predicates"]
        supported_keys = required_keys.copy()
        supported_keys.extend(["length", "description"])
        for info in self.tests_info:
            info_keys = list(info.keys())
            all_required_in = all(required in info_keys for required in required_keys)
            all_keys_supported = all(info in supported_keys for info in info_keys)
            if all_required_in and all_keys_supported:
                result.append(info)
        return result

    """
    -u predicate podmienky je mozne pouzit konstantu "XTEST" ktora nahradza akykolvek test name
    -"XTEST" sa moze pouzit ako sucast tag_name, napr: "XTEST_ok" alebo "scoring_XTEST"
    """
    def get_tests_info(self):
        # tests_info

        success = {
            'identifier': 1,
            'visualization': "ok",
            'description': "test passsed",
            'predicates': [{'predicate': ["XTEST_ok"], 'color': 'green'}]
        }
        tests_info = [success]
        return tests_info


    def get_solution_info(self):
        # sorting by id: [... 3 2 1]

        # default info
        date = {
            'identifier': 1,
            'visualization': "last_testing.1", # vypise sa ak existuje tag #last_testing
            'length': 15, #10/03/22-15:30
            'description': "datetime of last test",
            'predicates': []
        }
        status = {
            'identifier': 2,
            'visualization': 'T',
            'description': "was tested -- tag added at the end of testsuite.sh",
            'predicates': [
                {'predicate': ['last_testing'], 'color': ''} # tag: last_testing sa prida na konci testovania
            ]
        }
        group = {
            'identifier': 3,
            'visualization': 'G',
            'description': "is group project",
            'predicates': [
                {'predicate': ['group'], 'color': ''}
            ]
        }
        plagiat = {
            'identifier': 4,
            'visualization': '!!',
            'description': "is plagiat",
            'predicates': [
                {'predicate': ['plag'], 'color': 'red'}
            ]
        }

        # test results
        """
        test1 = {
            'identifier': 8,
            'visualization': '.',
            'description': "test1 result",
            'predicates': [
                {'predicate': ['test1_fail'], 'color': 'red'},
                {'predicate': ['test1_ok'], 'color': 'green'}
            ]
        }
        test2 = {
            'identifier': 7,
            'visualization': '.',
            'description': "test2 result",
            'predicates': [
                {'predicate': ['test2_fail'], 'color': 'red'},
                {'predicate': ['test2_ok'], 'color': 'green'}
            ]
        }
        """

        solution_info = [date, status, group, plagiat]
        # solution_info = [date, status, group, plagiat, test1, test2]
        return solution_info

