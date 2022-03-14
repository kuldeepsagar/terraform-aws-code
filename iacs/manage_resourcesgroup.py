import sys
import os
import csv
import json
import pandas as pd
import os
import csv_to_json1 as csv_to_json1
#from az.cli import az
import counter as counter
from python_terraform import *
#from az.cli import az
root_dir = os.path.dirname(__file__)
def getExcelSheetNames(dir, files, section):
    multifiles = [x for x in files if x.startswith("multi") and x.endswith(section+".xlsx")]

    returnList=[]
    for file in multifiles:
        wb = openpyxl.load_workbook(dir + "/" + file)
        for sheet in wb.sheetnames:
            returnList.append("("+file+")"+"("+sheet+")")

    return returnList

def processLanguageArgument(arg):
    if "/" in arg:
        language = arg.split("/")[0]
        profile = arg.split("/")[1]
    else:
        language = arg
        profile = ""
    return language, profile

readExcel=True
try:
    import openpyxl
except ImportError as e:
    print("you can't create TIFs in excel. Must install openpyxl")
    readExcel=False
    pass  # module doesn't exist, deal with it.


counter.initialize()
listOfLanguages = ["terraform", "terraform_old", "cfn", "arm"]
all_sections_in_cfn = ["Metadata", "Parameters", "Rules", "Mappings", "Conditions", "Transform", "Resources", "Outputs", "Template"]
all_sections_in_arm = ["Modules", "Resources"]
all_sections_in_terraform = ["resource", "data", "module", "output"]

language=''
profile=''
if (len(sys.argv) > 1):
    language, profile = processLanguageArgument(sys.argv[1])
    print(language)
    if language not in listOfLanguages:
        print("1. specify one of the following languages as the option: {0}".format(listOfLanguages))
        exit()
else:
    print("2. specify one of the following languages as the option: {0}".format(listOfLanguages))
    exit()

resourceGroupName=''
if (len(sys.argv) > 2):
    resourceGroupName = sys.argv[2]
    #t = Terraform(working_dir=resourceGroupName)
else:
    print("provide a resource group name")
    exit()
print("The resource group name is: ", resourceGroupName)
files = os.listdir(resourceGroupName)


if language == "terraform":
    #load json object which will be merged with the resource groups to create the resource groups
    with open(root_dir + 'templates/main.tf.json', 'r') as f:  # open json file
        all_resources = json.loads(f.read()) # load json content
    with open(root_dir + 'templates/variables_template.tf.json', 'r') as f: # open the parameters json file
        parameters = json.loads(f.read()) # load json content

    files = os.listdir(resourceGroupName)
    
    resource_files = [x for x in files if x.endswith(".csv") and x.startswith("resource") or 
                                          x.endswith(".xlsx") and readExcel and x.startswith("resource")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "resource")
    resource_files = resource_files + files_multi
    print("files of Resource:")
    print(resource_files)

    data_files = [x for x in files if x.endswith(".csv") and x.startswith("data") or 
                                          x.endswith(".xlsx") and readExcel and x.startswith("data")]

    files_multi = getExcelSheetNames(resourceGroupName, files, "data")
    data_files = data_files + files_multi
    print("files of Data:")
    print(data_files)
    

    module_files = [x for x in files if x.endswith(".csv") and x.startswith("module") or 
                                          x.endswith(".xlsx") and readExcel and x.startswith("module")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "module")
    module_files = module_files + files_multi
    print("files of module:")
    print(module_files)

    output_files = [x for x in files if x.endswith(".csv") and x.startswith("output") or 
                                          x.endswith(".xlsx") and readExcel and x.startswith("output")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "output")
    output_files = output_files + files_multi
    print("files of output:")
    print(output_files)

    print("*********************************************************************")
    for f in data_files:
        print("************ data resources file being processed")
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "data", all_sections_in_terraform, ".", profile)
        print("all data resources")
        print(all_resources['data'])
        if (all_resources['data'] == {}):
            all_resources['data'][type] = []

        if ((type in all_resources['data']) == False):
            all_resources['data'][type] = []
            
        all_resources['data'][type] = all_resources['data'][type] + resources

    for f in resource_files:
        print("************ resource file being processed")
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "resource", all_sections_in_terraform, ".", profile)
        print("all resources so far")
        print(all_resources['resource'])
        if (all_resources['resource'] == {}):
            all_resources['resource'][type] = []

        if ((type in all_resources['resource']) == False):
            all_resources['resource'][type] = []
            
        all_resources['resource'][type] = all_resources['resource'][type] + resources

    for f in module_files:
        print("************ module file being processed")
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "module", all_sections_in_terraform, ".", profile)
        print("all modules so far")
        print(all_resources['module'])
        print(resources)
        # for obj in resources:
        #    print(obj)
        #    all_resources['module'][obj] = resources[obj]
        all_resources['module'] = all_resources['module'] + resources

    for f in output_files:
        print("************ Output file being processed")
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "output", all_sections_in_terraform, ".", profile)
        print("all outputs so far")
        print(all_resources['output'])
        print(resources)
        # for obj in resources:
        #    print(obj)
        #    all_resources['module'][obj] = resources[obj]
        all_resources['output'] = all_resources['output'] + resources

    all_resources = csv_to_json1.cleanJson(all_resources)
    csv_to_json1.printJson(all_resources)

    with open(resourceGroupName + '/generated_logic.tf.json', 'w') as outfile:
        json.dump(all_resources, outfile, indent=4)

    with open(resourceGroupName + '/generated_parameters.tf.json', 'w') as outfile:
        json.dump(parameters, outfile, indent=4)
elif language == "terraform_old":
    resource_files = [x for x in files if x.endswith(".csv") and not(x.startswith("data")) and not(x.startswith("module")) and not(x.startswith("output")) or x.endswith(".xlsx") and readExcel and not(x.startswith("~$")) and not(x.startswith(".")) and not(x.startswith("data")) and not(x.startswith("module")) and not(x.endswith("tfstate")) and not(x.startswith("output"))  ]
    print("files of Resources:")
    print(resource_files)

    data_files = [x for x in files if x.endswith(".csv") and x.startswith("data") and not(x.startswith("output")) or x.endswith(".xlsx") and readExcel and not(x.startswith("~$")) and not(x.startswith(".")) and x.startswith("data") and not(x.endswith("tfstate")) and not(x.startswith("output")) ]
    print("files of Data resources:")
    print(data_files)

    module_files = [x for x in files if x.endswith(".csv") and x.startswith("module") or x.endswith(".xlsx") and readExcel and not(x.startswith("~$")) and not(x.startswith(".")) and x.startswith("module") and not(x.endswith("tfstate")) and not(x.startswith("output")) ]
    print("files of Module resources:")
    print(module_files)

    output_files = [x for x in files if x.endswith(".csv") and x.startswith("output") or x.endswith(".xlsx") and readExcel and x.startswith("output")  ]
    print("files of Output values:")
    print(output_files)

    #load json object which will be merged with the resource groups to create the resource groups
    with open('templates\\main.tf.json', 'r') as f:  # open json file
        all_resources = json.loads(f.read()) # load json content
    with open('templates\\variables_template.tf.json', 'r') as f: # open the parameters json file
        parameters = json.loads(f.read()) # load json content

    for f in data_files:
        print("************ data resources file being processed")
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '\\' + f)
        print("all data resources")
        print(all_resources['data'])
        if (all_resources['data'] == {}):
            all_resources['data'][type] = []

        if ((type in all_resources['data']) == False):
            all_resources['data'][type] = []
            
        all_resources['data'][type] = all_resources['data'][type] + resources

    for f in resource_files:
        print("************ resource file being processed")
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '\\' + f)
        print("all resources so far")
        print(all_resources['resource'])
        if (all_resources['resource'] == {}):
            all_resources['resource'][type] = []

        if ((type in all_resources['resource']) == False):
            all_resources['resource'][type] = []
            
        all_resources['resource'][type] = all_resources['resource'][type] + resources

    for f in module_files:
        print("************ module file being processed")
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '\\' + f)
        print("all modules so far")
        print(all_resources['module'])
        print(resources)
        # for obj in resources:
        #    print(obj)
        #    all_resources['module'][obj] = resources[obj]
        all_resources['module'] = all_resources['module'] + resources

    for f in output_files:
        print("************ Output file being processed")
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '\\' + f)
        print("all outputs so far")
        print(all_resources['output'])
        print(resources)
        # for obj in resources:
        #    print(obj)
        #    all_resources['module'][obj] = resources[obj]
        all_resources['output'] = all_resources['output'] + resources


    all_resources = csv_to_json1.cleanJson(all_resources)
    csv_to_json1.printJson(all_resources)


    with open(resourceGroupName + '\\generated_logic.tf.json', 'w') as outfile:
        json.dump(all_resources, outfile, indent=4)

    with open(resourceGroupName + '\\generated_parameters.json', 'w') as outfile:
        json.dump(parameters, outfile, indent=4)
elif language == "cfn": #********************************************************for CLOUDFORMATION
    parameters_files = [x for x in files if x.endswith(".csv") and x.startswith("Parameters") or 
                                          x.endswith(".xlsx") and x.startswith("Parameters")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "Parameters")
    parameters_files = parameters_files + files_multi
    print("files of Parameters:")
    print(parameters_files)

    template_files = [x for x in files if x.endswith(".csv") and x.startswith("Template") or 
                                          x.endswith(".xlsx") and x.startswith("Template")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "Template")
    template_files = template_files + files_multi
    print("files of Template:")
    print(template_files)    

    print("Here is were you will do the work for cfn")
    resource_files = [x for x in files if x.endswith(".csv") and x.startswith("Resources") or 
                                          x.endswith(".xlsx") and x.startswith("Resources")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "Resources")
    resource_files = resource_files + files_multi
    print("files of Resources:")
    print(resource_files)

    metadata_files = [x for x in files if x.endswith(".csv") and x.startswith("Metadata") or 
                                          x.endswith(".xlsx") and x.startswith("Metadata")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "Metadata")
    metadata_files = metadata_files + files_multi
    print("files of Metadata:")
    print(metadata_files)

    rules_files = [x for x in files if x.endswith(".csv") and x.startswith("Rules") or 
                                          x.endswith(".xlsx") and x.startswith("Rules")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "Rules")
    rules_files = rules_files + files_multi
    print("files of Rules:")
    print(rules_files)

    mappings_files = [x for x in files if x.endswith(".csv") and x.startswith("Mappings") or 
                                          x.endswith(".xlsx") and x.startswith("Mappings")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "Mappings")
    mappings_files = mappings_files + files_multi
    print("files of Mappings:")
    print(mappings_files)

    conditions_files = [x for x in files if x.endswith(".csv") and x.startswith("Conditions") or 
                                          x.endswith(".xlsx") and x.startswith("Conditions")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "Conditions")
    conditions_files = conditions_files + files_multi
    print("files of Conditions:")
    print(conditions_files)

    transform_files = [x for x in files if x.endswith(".csv") and x.startswith("Transform") or 
                                          x.endswith(".xlsx") and x.startswith("Transform")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "Transform")
    transform_files = transform_files + files_multi
    print("files of Transform:")
    print(transform_files)

    outputs_files = [x for x in files if x.endswith(".csv") and x.startswith("Outputs") or 
                                          x.endswith(".xlsx") and x.startswith("Outputs")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "Outputs")
    outputs_files = outputs_files + files_multi
    print("files of Outputs:")
    print(outputs_files)

    #load json object which will be merged with the resource groups to create the resource groups
    with open('templates/cfn.template.json', 'r') as f:  # open json file
        all_resources = json.loads(f.read()) # load json content
    with open('templates/cfn.parameters.json', 'r') as f: # open the parameters json file
        parameters = json.loads(f.read()) # load json content

    for f in parameters_files:
        print("************ {0} parameters file being processed".format(language))
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "Parameters", all_sections_in_cfn, ".")
        all_resources['Parameters'].update(resources)
        print("*******************")
        print(parameters)
        print(type)
        parameters = parameters + type # because both are lists

    for f in resource_files:
        print("************ {0} resource file being processed".format(language))
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "Resources", all_sections_in_cfn, ".")
        all_resources['Resources'].update(resources)

    for f in metadata_files:
        print("************ {0} metadata file being processed".format(language))
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "Metadata", all_sections_in_cfn, ".")
        all_resources['Metadata'].update(resources)        

    for f in rules_files:
        print("************ {0} rules file being processed".format(language))
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "Rules", all_sections_in_cfn, ".")
        all_resources['Rules'].update(resources)

    for f in mappings_files:
        print("************ {0} mappings file being processed".format(language))
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "Mappings", all_sections_in_cfn, "#")
        all_resources['Mappings'].update(resources)        

    for f in conditions_files:
        print("************ {0} conditions file being processed".format(language))
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "Conditions", all_sections_in_cfn, ".")
        all_resources['Conditions'].update(resources)

    for f in transform_files:
        print("************ {0} transform file being processed".format(language))
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "Transform", all_sections_in_cfn, ".")
        all_resources['Transform'].update(resources)        

    for f in outputs_files:
        print("************ {0} outputs file being processed".format(language))
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "Outputs", all_sections_in_cfn, ".")
        all_resources['Outputs'].update(resources)

    for f in template_files:
        print("************ {0} template file being processed".format(language))
        #print(type(f))
        resources, type, xxx = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "Template", all_sections_in_cfn, ".")
        all_resources.update(resources)


    all_resources = csv_to_json1.cleanJson(all_resources)
    csv_to_json1.printJson(all_resources)

    with open(resourceGroupName + '/generated_logic.json', 'w') as outfile:
        json.dump(all_resources, outfile, indent=4)

    with open(resourceGroupName + '/generated_parameters.json', 'w') as outfile:
        json.dump(parameters, outfile, indent=4)
elif language == "arm":

    #load json object which will be merged with the resource groups to create the resource groups
    with open(root_dir + '/templates/arm_resourcegroup_template.json', 'r') as f:  # open json file
        all_resources = json.loads(f.read()) # load json content
    with open(root_dir + '/templates/arm_parameters_template.json', 'r') as f: # open the parameters json file
        parameters = json.loads(f.read()) # load json content

    if profile != "":
        profile = '/profiles/arm/' + profile + '.json'
    else:
        profile = '/profiles/arm/profile-1.0.json'

    print(profile)
    with open(root_dir + profile, 'r') as f:  # open json file
        profile = json.loads(f.read()) # load json content

    #files = os.listdir(resourceGroupName)

    print("Here is were you will do the work for arm")
    modules_files = [x for x in files if x.endswith(".csv") and x.startswith("Modules") or 
                                          x.endswith(".xlsx") and readExcel and x.startswith("Modules")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "Modules")
    modules_files = modules_files + files_multi
    print("files of Modules:")
    print(modules_files)
    
    resources_files = [x for x in files if x.endswith(".csv") and x.startswith("Resources") or 
                                          x.endswith(".xlsx") and readExcel and x.startswith("Resources")]
    files_multi = getExcelSheetNames(resourceGroupName, files, "Resources")
    resources_files = resources_files + files_multi
    print("files of Resources:")
    print(resources_files)

    #other_files = [x for x in files if x.endswith(".csv") and not (x.startswith("Resources") or x.startswith("Modules") or x.startswith("~$")) or 
    #                                      x.endswith(".xlsx") and readExcel and not (x.startswith("Resources") or x.startswith("Modules") or x.startswith("~$"))]
    #print("files which are not starting with a predefined token:")
    #print(other_files)
    # arm_files = [x for x in files if x.endswith(".csv") or x.endswith(".xlsx") and readExcel and not(x.startswith("~$"))]

    for f in modules_files:
        print("************ modules file being processed")
        print(type(f))
        jf, pf, pJf = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "Modules", all_sections_in_arm, "_", profile)
        all_resources['resources'] = all_resources['resources'] + jf
        parameters['parameters'].update(pf)
        all_resources['parameters'].update(pJf)

    for f in resources_files:
        print("************ resources file being processed")
        print(type(f))
        jf, pf, pJf = csv_to_json1.generateFullJson(resourceGroupName + '/' + f, language, f, "Resources", all_sections_in_arm, "_", profile)
        all_resources['resources'] = all_resources['resources'] + jf
        parameters['parameters'].update(pf)
        all_resources['parameters'].update(pJf)

    
    all_resources = csv_to_json1.cleanJson(all_resources)
    csv_to_json1.printJson(all_resources)

    with open(resourceGroupName + '/generated_logic.json', 'w') as outfile:
        json.dump(all_resources, outfile, indent=4)

    with open(resourceGroupName + '/generated_parameters.json', 'w') as outfile:
        json.dump(parameters, outfile, indent=4)
else:
    print("language is not defined:{0}".format(language))
    exit()
print("*************The code has been generated*****************")
exit()
executeOption = "plan"
if (len(sys.argv) > 2 and sys.argv[2] == "create"):
    executeOption = "create"
return_code, stdout, stderr = t.cmd(sys.argv[2])
#az deployment group create --confirm-with-what-if --mode %6 --no-prompt true --resource-group %1 --name %2 --template-file %3 --parameters @%4
# On 0 (SUCCESS) print result_dict, otherwise get info from `logs`


if return_code == 0:
    print("{0}".format(stdout))
else:
    print(stderr)
