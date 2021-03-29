from xml.etree import ElementTree, ElementInclude
import re
import csv
import os


class BaseParser:
    def __init__(self, name_file_read):
        self.tree = ElementTree.parse(name_file_read)
        self.root = self.tree.getroot()
        self.repository = {}
        self.dict_name = []

    def add_name_file(self) -> None:
        """Функция для добавления названия файла"""
        self.repository["INPUT_FILE_NAME"].append(name_file_read)

    def parser_NESW(self):
        if len(self.repository["NESW"]) == 0:
            NESW_dict = self.root.findall(
                ".//{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}managedElement"
            )
            NESW = NESW_dict[0].attrib["swVersion"]
            self.repository["NESW"].append(NESW)
        else:
            self.repository["NESW"].append(self.repository["NESW"][0])

    def data_preparation(self, name_file_write: str) -> None:
        """Функция читает выходной файл пример и заполняется словарь
        repository названиями столбцов. Так же создается список из
        названий и номера(если он есть) для дальнейшего парсинга
        данных"""
        csvfile = open(name_file_write, "r")
        csvFileArray = []
        for row in csv.reader(csvfile, delimiter="."):
            csvFileArray.append(row)
        for i in csvFileArray[0]:
            name_list = i.split(",")
            for j in name_list:
                self.repository[j] = []
        for key in self.repository.keys():
            if re.search("\d+", key):
                key_list = key.split("_")
                self.dict_name.append(key_list)
            else:
                self.dict_name.append([key])

    def parsing_fileHeader(self) -> None:
        """Функция для добавления данных из заголовка"""
        if len(self.repository["RNC"]) == 0:
            element_tag = "{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}fileHeader"
            answer = self.root.findall(element_tag)
            element = answer[0].attrib
            string = element.get("dnPrefix", "no keys")
            RNC = re.search(r"(?<=SubNetwork=).*?(?=,SubNetwork)", string).group(0)
            self.repository["RNC"].append(RNC)
        else:
            self.repository["RNC"].append(self.repository["RNC"][0])

    def parsing_fileFooter(self) -> None:
        """Функция для добавления данных из 'подвала'   """
        if len(self.repository["DATETIME"]) == 0:
            element_tag = ".//{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measCollec"
            answer = self.tree.findall(element_tag)
            element = answer[1].attrib
            string = element.get("endTime", "no keys")
            date = re.sub(r"[^0-9]", "", string)
            self.repository["DATETIME"].append(date)
        else:
            self.repository["DATETIME"].append(self.repository["DATETIME"][0])

    def parser_data(self, search: str, answer: str, i: int) -> None:
        attrib_dict = {}
        for j in range(len(answer[i])):
            if answer[i][j].text != None:
                key_attrib_dict = answer[i][j].attrib.get("p", "no key")
                attrib_dict[answer[i][j].text.upper()] = key_attrib_dict
        for j in range(len(answer[i])):
            if search in answer[i][j].attrib:
                for key in self.dict_name:
                    if len(key) == 1:
                        if key[0] in attrib_dict:
                            item = int(attrib_dict[key[0]])
                            value = answer[i][j][item - 1].text
                            self.repository.setdefault(key[0], [value])
                            self.repository[key[0]].append(value)
                    if len(key) > 1:
                        if key[0] in attrib_dict:

                            item = int(attrib_dict[key[0]])
                            value_list = answer[i][j][item - 1].text.split(",")
                            name_repo = "_".join(key)
                            value_repo = value_list[int(key[1])]

                            self.repository.setdefault(name_repo, [value_repo])
                            self.repository[name_repo].append(value_repo)

    def parser_name(self, search, answer, i) -> None:
        for j in range(len(answer[i])):
            if search in answer[i][j].attrib:

                PT900S = answer[8][2].attrib["duration"]
                GP = re.search(r"(?<=PT).*?(?=S)", PT900S).group(0)
                self.repository["GP"].append(GP)
                self.add_name_file()
                self.parser_NESW()
                self.parsing_fileFooter()
                self.parsing_fileHeader()
                string = answer[i][j].attrib.get(search, "no keys")

                managedElement = re.search(
                    r"(?<=ManagedElement=).*?(?=,)", string
                ).group(0)
                self.repository["ManagedElement"].append(managedElement)

                equipment = re.search(r"(?<=Equipment=).*?(?=,)", string).group(0)
                self.repository["Equipment"].append(equipment)

                FieldReplaceableUnit = re.search(
                    r"(?<=FieldReplaceableUnit=).*?(?=,)", string
                ).group(0)
                self.repository["FieldReplaceableUnit"].append(FieldReplaceableUnit)

                BbProcessingResource = re.search(
                    r"(?<=BbProcessingResource=).*?(?=$)", string
                ).group(0)
                self.repository["BbProcessingResource"].append(BbProcessingResource)

    def base_parser(self, search_name) -> None:
        """Основная функция парсера документа"""
        element_tag = ".//{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measInfo"
        answer = self.root.findall(element_tag)

        search = "measObjLdn"
        index_list = []
        for item in range(len(answer)):
            if answer[item].attrib["measInfoId"].endswith(search_name):
                index_list.append(int(item))
        for i in index_list:
            self.parser_data(search, answer, i)

    def save_file(self, folder_name: str, file_name: str) -> None:
        """Функция для сохранения данных в файл csv"""
        os.mkdir(f"{folder_name}")
        with open(f"{folder_name}/{file_name}.csv", "w") as f:
            wr = csv.writer(f)
            wr.writerow((self.repository.keys()))
            list_value = self.repository.values()
            for item in range(len(self.repository["ManagedElement"])):
                list_write = []
                for i in list_value:
                    try:
                        list_write.append(i[item])
                    except:
                        list_write.append(" ")
                wr.writerow(list_write)


class EDchResources(BaseParser):
    def parser_name(self, search: str, answer: str, i: int) -> None:
        for j in range(len(answer[i])):
            if search in answer[i][j].attrib:

                PT900S = answer[i][2].attrib["duration"]
                GP = re.search(r"(?<=PT).*?(?=S)", PT900S).group(0)
                self.repository["GP"].append(GP)
                self.add_name_file()
                self.parser_NESW()
                self.parsing_fileFooter()
                self.parsing_fileHeader()

                string = answer[i][j].attrib.get(search, "no keys")
                managedElement = re.search(
                    r"(?<=ManagedElement=).*?(?=,)", string
                ).group(0)
                self.repository["ManagedElement"].append(managedElement)

                NodeBFunction = re.search(r"(?<=NodeBFunction=).*?(?=,)", string).group(
                    0
                )
                self.repository.setdefault("NodeBFunction", list([NodeBFunction]))
                self.repository["NodeBFunction"].append(NodeBFunction)

                NodeBLocalCellGroup = re.search(
                    r"(?<=NodeBLocalCellGroup=).*?(?=,)", string
                ).group(0)
                self.repository.setdefault("NodeBLocalCellGroup", [NodeBLocalCellGroup])
                self.repository["NodeBLocalCellGroup"].append(NodeBLocalCellGroup)

                NodeBLocalCell = re.search(
                    r"(?<=NodeBLocalCell=).*?(?=,)", string
                ).group(0)
                self.repository.setdefault("NodeBLocalCell", [NodeBLocalCell])
                self.repository["NodeBLocalCell"].append(NodeBLocalCell)

                NodeBSectorCarrier = re.search(
                    r"(?<=NodeBSectorCarrier=).*?(?=,)", string
                ).group(0)
                self.repository.setdefault("NodeBSectorCarrier", [NodeBSectorCarrier])
                self.repository["NodeBSectorCarrier"].append(NodeBSectorCarrier)

                EDchResources = re.search(r"(?<=EDchResources=).*?(?=$)", string).group(
                    0
                )
                self.repository.setdefault("EDchResources", [EDchResources])
                self.repository["EDchResources"].append(EDchResources)


class EUtranCellFDD(BaseParser):
    def parser_name(self, search: str, answer: str, i: int) -> None:
        for j in range(len(answer[i])):
            if search in answer[i][j].attrib:

                PT900S = answer[i][2].attrib["duration"]
                GP = re.search(r"(?<=PT).*?(?=S)", PT900S).group(0)
                self.repository["GP"].append(GP)
                self.add_name_file()
                self.parser_NESW()
                self.parsing_fileFooter()
                self.parsing_fileHeader()

                string = answer[i][j].attrib.get(search, "no keys")
                managedElement = re.search(
                    r"(?<=ManagedElement=).*?(?=,)", string
                ).group(0)
                self.repository["ManagedElement"].append(managedElement)
                ENodeBFunction = re.search(
                    r"(?<=ENodeBFunction=).*?(?=,)", string
                ).group(0)
                self.repository["ENodeBFunction"].append(ENodeBFunction)
                EUtranCellFDD = re.search(r"(?<=EUtranCellFDD=).*?(?=$)", string).group(
                    0
                )
                self.repository["EUtranCellFDD"].append(EUtranCellFDD)


class HsDschResources(BaseParser):
    def parser_name(self, search: str, answer: str, i: int) -> None:
        for j in range(len(answer[i])):
            if search in answer[i][j].attrib:

                PT900S = answer[i][2].attrib["duration"]
                GP = re.search(r"(?<=PT).*?(?=S)", PT900S).group(0)
                self.repository["GP"].append(GP)
                self.add_name_file()
                self.parser_NESW()
                self.parsing_fileFooter()
                self.parsing_fileHeader()

                string = answer[i][j].attrib.get(search, "no keys")
                managedElement = re.search(
                    r"(?<=ManagedElement=).*?(?=,)", string
                ).group(0)
                self.repository["ManagedElement"].append(managedElement)
                NodeBFunction = re.search(r"(?<=NodeBFunction=).*?(?=,)", string).group(
                    0
                )
                self.repository["NodeBFunction"].append(NodeBFunction)
                HsDschResources = re.search(
                    r"(?<=HsDschResources=).*?(?=$)", string
                ).group(0)
                self.repository["HsDschResources"].append(HsDschResources)


class HsDschResources_2(BaseParser):
    def parser_name(self, search: str, answer: str, i: int) -> None:
        for j in range(len(answer[i])):
            if search in answer[i][j].attrib:

                PT900S = answer[i][2].attrib["duration"]
                GP = re.search(r"(?<=PT).*?(?=S)", PT900S).group(0)
                self.repository["GP"].append(GP)
                self.add_name_file()
                self.parser_NESW()
                self.parsing_fileFooter()
                self.parsing_fileHeader()

                string = answer[i][j].attrib.get(search, "no keys")
                managedElement = re.search(
                    r"(?<=ManagedElement=).*?(?=,)", string
                ).group(0)
                self.repository["ManagedElement"].append(managedElement)
                NodeBFunction = re.search(r"(?<=NodeBFunction=).*?(?=,)", string).group(
                    0
                )
                self.repository["NodeBFunction"].append(NodeBFunction)
                HsDschResources = re.search(
                    r"(?<=HsDschResources=).*?(?=$)", string
                ).group(0)
                self.repository["HsDschResources"].append(HsDschResources)


class UtranCellRelation(BaseParser):
    def parser_name(self, search: str, answer: str, i: int) -> None:
        for j in range(len(answer[i])):
            if search in answer[i][j].attrib:
                PT900S = answer[8][2].attrib["duration"]
                GP = re.search(r"(?<=PT).*?(?=S)", PT900S).group(0)
                self.repository["GP"].append(GP)
                self.add_name_file()
                self.parser_NESW()
                self.parsing_fileFooter()
                self.parsing_fileHeader()
                string = answer[i][j].attrib.get(search, "no keys")
                managedElement = re.search(
                    r"(?<=ManagedElement=).*?(?=,)", string
                ).group(0)
                self.repository["ManagedElement"].append(managedElement)

                ENodeBFunction = re.search(
                    r"(?<=ENodeBFunction=).*?(?=,)", string
                ).group(0)
                self.repository["ENodeBFunction"].append(ENodeBFunction)

                EUtranCellFDD = re.search(r"(?<=EUtranCellFDD=).*?(?=,)", string).group(
                    0
                )
                self.repository["EUtranCellFDD"].append(EUtranCellFDD)

                UtranFreqRelation = re.search(
                    r"(?<=UtranFreqRelation=).*?(?=,)", string
                ).group(0)
                self.repository["UtranFreqRelation"].append(UtranFreqRelation)

                UtranCellRelation = re.search(
                    r"(?<=UtranCellRelation=).*?(?=$)", string
                ).group(0)
                self.repository["UtranCellRelation"].append(UtranCellRelation)


# BbProcessingResource
name_file_read = "in/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_statsfile.bin"
name_file_write = "out/BbProcessingResource/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_BbProcessingResource.csv"
BbProcessingResource_object = BaseParser(name_file_read)
BbProcessingResource_object.data_preparation(name_file_write)
BbProcessingResource_object.base_parser("BbProcessingResource")
BbProcessingResource_object.save_file(
    "test____BbProcessingResource",
    "ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_BbProcessingResource",
)

# EDchResources
name_file_read = "in/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_statsfile.bin"
name_file_write = "out/EDchResources/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_EDchResources.csv"
EDchResources_object = EDchResources(name_file_read)
EDchResources_object.data_preparation(name_file_write)
EDchResources_object.base_parser("EDchResources")
EDchResources_object.save_file(
    "test____EDchResources",
    "ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_EDchResources.csv",
)

# EUtranCellFDD
name_file_read = "in/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_statsfile.bin"
name_file_write = "out/EUtranCellFDD/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_EUtranCellFDD.csv"
EUtranCellFDD_object = EUtranCellFDD(name_file_read)
EUtranCellFDD_object.data_preparation(name_file_write)
EUtranCellFDD_object.base_parser("EUtranCellFDD")
EUtranCellFDD_object.save_file(
    "test____EUtranCellFDD",
    "ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_EUtranCellFDD.csv",
)

# HsDschResources
name_file_read = "in/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_statsfile.bin"
name_file_write = "out/HsDschResources/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_HsDschResources.csv"
HsDschResources_object = HsDschResources(name_file_read)
HsDschResources_object.data_preparation(name_file_write)
HsDschResources_object.base_parser("HsDschResources")
HsDschResources_object.save_file(
    "test____HsDschResources",
    "ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_HsDschResources.csv",
)

# UtranCellRelation
name_file_read = "in/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_statsfile.bin"
name_file_write = "out/UtranCellRelation/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_UtranCellRelation.csv"
UtranCellRelation_object = UtranCellRelation(name_file_read)
UtranCellRelation_object.data_preparation(name_file_write)
UtranCellRelation_object.base_parser("UtranCellRelation")
UtranCellRelation_object.save_file(
    "test____UtranCellRelation",
    "ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_UtranCellRelation.csv",
)
