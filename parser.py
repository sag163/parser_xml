from xml.etree import ElementTree, ElementInclude
import re
import csv
import os


class BaseParser():
    def __init__(self, name_file_read):
        self.tree = ElementTree.parse(name_file_read)
        self.root = self.tree.getroot()    
        self.repository = {}
        self.dict_name = []

    def add_name_file(self):
        self.repository['INPUT_FILE_NAME'].append(name_file_read)

    def data_preparation(self, name_file_write):
        '''Функция читает выходной файл пример и заполняется словарь
        repository названиями столбцов. Так же создается список из
        названий и номера(если он есть) для дальнейшего парсинга
        данных'''
        csvfile = open(name_file_write, 'r')
        csvFileArray = []
        for row in csv.reader(csvfile, delimiter = '.'):
            csvFileArray.append(row)
        for i in csvFileArray[0]:
            name_list = i.split(',')
            for j in name_list:
                self.repository[j] = []

        for key in self.repository.keys():
            if re.search('\d+', key):
                key_list = key.split('_')
                self.dict_name.append(key_list)
            else:
                self.dict_name.append([key])
        print(self.repository)

        



    def parsing_fileHeader(self):
        element_tag = '{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}fileHeader'
        answer = self.root.findall(element_tag)
        element = answer[0].attrib
        string = element.get('dnPrefix', 'no keys')
        RNC = re.search(r"(?<=SubNetwork=).*?(?=,SubNetwork)", string).group(0)
        self.repository['RNC'].append(RNC)
        managedElement = re.search(r"(?<=MeContext=).*?(?=$)", string).group(0)
        #self.repository['ManagedElement'] = managedElement
        #print(self.repository)

    def parsing_fileFooter(self):
        element_tag = './/{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measCollec'
        answer = self.tree.findall(element_tag)
        element = answer[1].attrib
        string = element.get('endTime', 'no keys')
        self.repository['DATETIME'] = re.sub(r'[^0-9]', '', string)
        #print(self.repository)

    def base_parser(self, search_name):
        element_tag = './/{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measInfo'
        answer = self.root.findall(element_tag)
        search = 'measObjLdn'
        for i in range(len(answer)):
            if search_name in answer[i].attrib['measInfoId']:
                if len(answer[i]) > 20:
                    elem = answer[i][1].text
                    attrib_dict = {}
                    for j in range(len(answer[i])):
                        if answer[i][j].text != None:
                            key_attrib_dict = answer[i][j].attrib.get('p', 'no key')
                            attrib_dict[key_attrib_dict] = answer[i][j].text.upper()
                        if search  in answer[i][j].attrib:
                            string = answer[i][j].attrib.get(search, 'no keys')

                            managedElement = re.search(r"(?<=ManagedElement=).*?(?=,)", string).group(0)
                            self.repository['ManagedElement'].append(managedElement)

                            equipment = re.search(r"(?<=Equipment=).*?(?=,)", string).group(0)
                            self.repository['Equipment'].append(equipment)
                            
                            FieldReplaceableUnit = re.search(r"(?<=FieldReplaceableUnit=).*?(?=,)", string).group(0)
                            self.repository['FieldReplaceableUnit'].append(FieldReplaceableUnit)
                            
                            BbProcessingResource = re.search(r"(?<=BbProcessingResource=).*?(?=$)", string).group(0)
                            self.repository['BbProcessingResource'].append(BbProcessingResource)
                            #print(self.repository)


                            for w in range(len(answer[i][j])):
                                if ',' not in answer[i][j][w].text:
                                    self.add_name_file()
                                    key_attrib = answer[i][j][w].attrib['p']
                                    self.repository[attrib_dict[key_attrib]].append(answer[i][j][w].text)



    def save_file(self, folder_name, file_name):
        os.mkdir(f'{folder_name}')
        with open(f'{folder_name}/{file_name}.csv', 'w') as f:
            wr = csv.writer(f)
            wr.writerow((self.repository.keys()))
            list_value = self.repository.values()
            for item in range(len(self.repository['ManagedElement'])):
                list_write = []
                for i in list_value:
                    try:
                        list_write.append(i[item])
                        print(i[item])
                    except:
                        list_write.append(' ')
                wr.writerow(list_write)



name_file_read = 'in/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_statsfile.bin'
name_file_write = 'out/BbProcessingResource/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_BbProcessingResource.csv'
asdf = BaseParser(name_file_read)
asdf.data_preparation(name_file_write)
asdf.parsing_fileFooter()
asdf.parsing_fileHeader()
asdf.base_parser('BbProcessingResource')
asdf.save_file('test____BbProcessingResource', 'ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_BbProcessingResource')


class EDchResources(BaseParser):
    def parser_name(self, search_name):
        pass

    def base_parser(self, search_name):

        element_tag = './/{http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec}measInfo'
        answer = self.root.findall(element_tag)
        search = 'measObjLdn'
        index_list = []
        for item in range(len(answer)):
            if answer[item].attrib['measInfoId'].endswith(search_name):
                index_list.append(int(item))

        # выполняем парсинг второй части search_name
        i = index_list[1]
        attrib_dict = {}
        for j in range(len(answer[i])):
            if answer[i][j].text != None:
                key_attrib_dict = answer[i][j].attrib.get('p', 'no key')
                attrib_dict[answer[i][j].text.upper()] = key_attrib_dict
            if search  in answer[i][j].attrib:
                string = answer[i][j].attrib.get(search, 'no keys')
                managedElement = re.search(r"(?<=ManagedElement=).*?(?=,)", string).group(0)
                self.repository['ManagedElement'].append(managedElement)

                NodeBFunction = re.search(r"(?<=NodeBFunction=).*?(?=,)", string).group(0)
                self.repository.setdefault('NodeBFunction', list([NodeBFunction]))
                self.repository['NodeBFunction'].append(NodeBFunction)

                NodeBLocalCellGroup = re.search(r"(?<=NodeBLocalCellGroup=).*?(?=,)", string).group(0)
                self.repository.setdefault('NodeBLocalCellGroup', [NodeBLocalCellGroup])
                self.repository['NodeBLocalCellGroup'].append(NodeBLocalCellGroup)


                NodeBLocalCell = re.search(r"(?<=NodeBLocalCell=).*?(?=,)", string).group(0)
                self.repository.setdefault('NodeBLocalCell', [NodeBLocalCell])
                self.repository['NodeBLocalCell'].append(NodeBLocalCell)

                NodeBSectorCarrier = re.search(r"(?<=NodeBSectorCarrier=).*?(?=,)", string).group(0)
                self.repository.setdefault('NodeBSectorCarrier', [NodeBSectorCarrier])
                self.repository['NodeBSectorCarrier'].append(NodeBSectorCarrier)

                EDchResources = re.search(r"(?<=EDchResources=).*?(?=$)", string).group(0)
                self.repository.setdefault('EDchResources', [EDchResources])
                self.repository['EDchResources'].append(EDchResources)


        # for key in self.dict_name:
        #     self.add_name_file()
        #     if len(key) == 1:
        #         if key[0] in attrib_dict:
        #             item = int(attrib_dict[key[0]])
        #             value = answer[i][j][item-1].text
        #             self.repository.setdefault(key[0], [value])
        #             self.repository[key[0]].append(value)

        #     if len(key) > 1:
        #         if key[0] in attrib_dict:

        #             item = int(attrib_dict[key[0]])
        #             value_list = answer[i][j][item-1].text.split(',')
        #             name_repo = '_'.join(key)
        #             value_repo = value_list[int(key[1])]
        #             self.repository.setdefault(name_repo, [value_repo])
        #             self.repository[name_repo].append(value_repo)



        i = index_list[0]
        for i in a
        attrib_dict = {}

        for j in range(len(answer[i])):
            if answer[i][j].text != None:
                key_attrib_dict = answer[i][j].attrib.get('p', 'no key')
                attrib_dict[answer[i][j].text.upper()] = key_attrib_dict
            
            if search in answer[i][j].attrib:

                for key in self.dict_name:
                    
                    if len(key) == 1:
                        #print(key[0])
                        if key[0] in attrib_dict:
                            #print(key)
                            item = int(attrib_dict[key[0]])
                            value = answer[i][j][item-1].text
                            self.repository.setdefault(key[0], [value])
                            self.repository[key[0]].append(value)
                            # rint(key, item)p
                    if len(key) > 1:
                        if key[0] in attrib_dict:
                            #print(key[0])

                            item = int(attrib_dict[key[0]])
                            value_list = answer[i][j][item-1].text.split(',')
                            name_repo = '_'.join(key)
                            value_repo = value_list[int(key[1])]

                            self.repository.setdefault(name_repo, [value_repo])
                            self.repository[name_repo].append(value_repo)
        #print(self.repository)

class EUtranCellFDD(EDchResources):
    pass

name_file_read = 'in/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_statsfile.bin'
name_file_write = 'out/EDchResources/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_EDchResources.csv'
EDchResources = EDchResources(name_file_read)
EDchResources.data_preparation(name_file_write)
EDchResources.parsing_fileFooter()
EDchResources.parsing_fileHeader()
EDchResources.base_parser('EDchResources')
EDchResources.save_file('test____EDchResources', 'ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_EDchResources.csv')

# name_file_read = 'in/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_statsfile.bin'
# name_file_write = 'out/EUtranCellFDD/ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_EUtranCellFDD.csv'
# EUtranCellFDD = EUtranCellFDD(name_file_read)
# EUtranCellFDD.data_preparation(name_file_write)
# EUtranCellFDD.parsing_fileFooter()
# EUtranCellFDD.parsing_fileHeader()
# EUtranCellFDD.base_parser('EUtranCellFDD')
# EUtranCellFDD.save_file('test____EUtranCellFDD', 'ERAN3GNDB94_20201218133919_202012181315_1330_0500_RAN_59_BTS_59_01218_ULN_EUtranCellFDD.csv.csv')

