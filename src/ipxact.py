#!/usr/local/bin/python2.7
# encoding: utf-8
'''
ipxact -- Parser for IP-XACT (IEEE 1685) files.

ipxact is a tool for extracting information from IP-XACT files.

It defines classes_and_methods

@author:     Klaus Petersen
        
@copyright:  2014 Klaus Petersen
This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See the COPYING file for more details.

@license:    http://www.wtfpl.net/txt/copying/

@contact:    klauspetersen@gmail.com
@deffield    updated: Updated
'''


import sys
import os
import logging as log
import math
from lxml import etree

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2014-01-02'
__updated__ = '2014-01-02'

DEBUG = 1
TESTRUN = 0
PROFILE = 0

IPXACT_NS = '{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5}'

C_HEADER_DIV = "/*****************************************************************************/"

C_PRAGMA_ONCE = "#pragma once\n"

C_SPIRIT_TYPES = '''
typedef enum{
    SPIRIT_ACCESSTYPE_READWRITE,
    SPIRIT_ACCESSTYPE_READONLY,
    SPIRIT_ACCESSTYPE_WRITEONLY,
    SPIRIT_ACCESSTYPE_READWRITEONCE,
    SPIRIT_ACCESSTYPE_WRITEONCE
}SPIRIT_ACCESSTYPE_T;

typedef enum{
    SPIRIT_USAGETYPE_MEMORY, 
    SPIRIT_USAGETYPE_REGISTER,
    SPIRIT_USAGETYPE_RESERVED
} SPIRIT_USAGETYPE_T;

typedef enum{
    SPIRIT_TESTCONSTRAINTTYPE_UNCONSTRAINED,
    SPIRIT_TESTCONSTRAINTTYPE_RESTORE,
    SPIRIT_TESTCONSTRAINTTYPE_WRITEASREAD,
    SPIRIT_TESTCONSTRAINTTYPE_READONLY
} SPIRIT_TESTCONSTRAINTTYPE_T;

typedef enum{
    SPIRIT_MODIFIEDWRITEVALUETYPE_ONETOCLEAR,
    SPIRIT_MODIFIEDWRITEVALUETYPE_ONETOSET,
    SPIRIT_MODIFIEDWRITEVALUETYPE_ONETOTOGGLE,
    SPIRIT_MODIFIEDWRITEVALUETYPE_ZEROTOCLEAR, 
    SPIRIT_MODIFIEDWRITEVALUETYPE_ZEROTOSET,
    SPIRIt_MODIFIEDWRITEVALUETYPE_ZEROTOTOGGLE,
    SPIRIT_MODIFIEDWRITEVALUETYPE_CLEAR,
    SPIRIT_MODIFIEDWRITEVALUETYPE_SET,
    SPIRIT_MODIFIEDWRITEVALUETYPE_MODIFY
} SPIRIT_MODIFIEDWRITEVALUETYPE_T;

typedef enum{
    SPIRIT_READACTIONTYPE_CLEAR,
    SPIRIT_READACTIONTYPE_SET,
    SPIRIT_READACTIONTYPE_MODIFY
} SPIRIT_READACTIONTYPE_T;

typedef enum{
    SPIRIT_BOOL_FALSE,
    SPIRIT_BOOL_TRUE     
} SPIRIT_BOOL_TYPE;
'''


class intToHexStringError(Exception): 
    def __init__(self, message):
        Exception.__init__(self, "'%s'" % (message))

class intToBinStringError(Exception): 
    def __init__(self, message):
        Exception.__init__(self, "'%s'" % (message))
        
VHDL_HEADER = '''
library ieee;
use ieee.std_logic_1164.all;
use ieee.math_real.all;
use ieee.numeric_std.all;

package regs is
'''

VHDL_SPIRIT_TYPES = '''
    type spiritAccessType is (
        SPIRIT_ACCESSTYPE_READWRITE,
        SPIRIT_ACCESSTYPE_READONLY,
        SPIRIT_ACCESSTYPE_WRITEONLY,
        SPIRIT_ACCESSTYPE_READWRITEONCE,
        SPIRIT_ACCESSTYPE_WRITEONCE
    );

    type spiritUsageType is (
        SPIRIT_USAGETYPE_MEMORY, 
        SPIRIT_USAGETYPE_REGISTER,
        SPIRIT_USAGETYPE_RESERVED
    );

    type spiritTestconstraintType is (
        SPIRIT_TESTCONSTRAINTTYPE_UNCONSTRAINED,
        SPIRIT_TESTCONSTRAINTTYPE_RESTORE,
        SPIRIT_TESTCONSTRAINTTYPE_WRITEASREAD,
        SPIRIT_TESTCONSTRAINTTYPE_READONLY
    );

    type spiritModifiedWriteValueType is (
        SPIRIT_MODIFIEDWRITEVALUETYPE_ONETOCLEAR,
        SPIRIT_MODIFIEDWRITEVALUETYPE_ONETOSET,
        SPIRIT_MODIFIEDWRITEVALUETYPE_ONETOTOGGLE,
        SPIRIT_MODIFIEDWRITEVALUETYPE_ZEROTOCLEAR, 
        SPIRIT_MODIFIEDWRITEVALUETYPE_ZEROTOSET,
        SPIRIt_MODIFIEDWRITEVALUETYPE_ZEROTOTOGGLE,
        SPIRIT_MODIFIEDWRITEVALUETYPE_CLEAR,
        SPIRIT_MODIFIEDWRITEVALUETYPE_SET,
        SPIRIT_MODIFIEDWRITEVALUETYPE_MODIFY
    );

    type spiritReadActionType is (
        SPIRIT_READACTIONTYPE_CLEAR,
        SPIRIT_READACTIONTYPE_SET,
        SPIRIT_READACTIONTYPE_MODIFY
    );
    
    type spiritBoolType is (
         SPIRIT_BOOL_FALSE,
         SPIRIT_BOOL_TRUE     
    );
    '''
    
VHDL_FOOTER = '''

end package;
'''


C_LRM = "IP-XACT Standard/D4, December 19, 2007"

C_DESC = {
    'NAME'                : 'Name',
    'USAGE'               : 'Usage',
    'DESCRIPTION'         : 'Description',
    'BITOFFSET'           : 'Bit offset',
    'BITOFFSETLOW'        : 'Bit offset low',
    'BITOFFSETHIGH'       : 'Bit offset high',
    'BITWIDTH'            : 'Bit width',
    'VOLATILE'            : 'Volatile',
    'ACCESS'              : 'Access',
    'MODIFIEDWRITEVALUE'  : 'Modified write value',
    'TESTCONSTRAINT'      : 'Test constraint',
    'DIM'                 : 'Dimensions',
    'ADDRESSBLOCKOFFSET'  : 'Address block offset',
    'BASEADDRESSOFFSET'   : 'Base address offset',
    'SIZE'                : 'Size',
    'RESETVALUE'          : 'Reset value',
    'RESETMASK'           : 'Reset mask',
    'BASEADDRESS'         : 'Base address',
    'HIGHADDRESS'         : 'High address',
    'RANGE'               : 'Range',
    'WIDTH'               : 'Width',
    'READACTION'          : 'Read action',
    'TESTABLE'            : 'Is testable',
    'NUMBER'              : 'Register number',
    'NUMBEROFREGS'        : 'Number of registers'
          }

C_POSTFIX = {
    'NAME'                : 'NAME',
    'USAGE'               : 'USAGE',
    'DESCRIPTION'         : 'DESC',
    'BITOFFSET'           : 'BO',
    'BITOFFSETLOW'        : 'BOL',
    'BITOFFSETHIGH'       : 'BOH',
    'BITWIDTH'            : 'BW',
    'VOLATILE'            : 'VLT',
    'ACCESS'              : 'ACC',
    'MODIFIEDWRITEVALUE'  : 'MWV',
    'TESTCONSTRAINT'      : 'TC',
    'DIM'                 : 'DIM',
    'ADDRESSBLOCKOFFSET'  : 'ABO',
    'BASEADDRESSOFFSET'   : 'BAO',
    'SIZE'                : 'SIZE',
    'RESETVALUE'          : 'RSTVAL',
    'RESETMASK'           : 'RSTMSK',
    'BASEADDRESS'         : 'BA',
    'HIGHADDRESS'         : 'HA',
    'RANGE'               : 'RNG',
    'WIDTH'               : 'WIDTH',
    'READACTION'          : 'RDACT',
    'TESTABLE'            : 'TST',
    'NUMBER'              : 'NUM',
    'NUMBEROFREGS'        : 'NUMREGS'
           }

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg
    
def getComponentName(root):
    return root.find('./' + IPXACT_NS + 'name').text

def getAddressBlockElementList(root):
    return root.findall(".//%saddressBlock" % IPXACT_NS)
    
def getRegisterElementList(root):
    return root.findall(".//%sregister" % IPXACT_NS)

def getFieldElementList(root):
    return root.findall(".//%sfield" % IPXACT_NS)

def getEnumElementList(root):
    return root.findall(".//%senumeratedValues" % IPXACT_NS)

        
def getMaxLengtOfColumnsAsList(xList):
    maxLengthList = list()
    for colList in zip(*xList):
        colMaxLen = 0
        for col in colList:
            if len(col) > colMaxLen:
                colMaxLen = len(col)
        maxLengthList.append(colMaxLen)
    return maxLengthList

    
                                 
def ifNotNoneReturnText(element):
    if element is not None:
        return element.text
    else:
        return None
 
def openXMLFileReturnRoot(path):
    path = os.path.normpath(path)
    if os.path.exists(os.path.abspath(path)):
        log.info("Opening file: %s", path)
        tree = etree.parse(path)
        root = tree.getroot() 
        return root
    else:
        raise IOError(2, "File does not exist, file:%s" % os.path.abspath(path))
    
     
def convAccessTypeToDefine(accessTypeString):
    if accessTypeString == "read-write":
        return "SPIRIT_ACCESSTYPE_READWRITE"
    elif accessTypeString == "read-only":
        return "SPIRIT_ACCESSTYPE_READONLY"
    elif accessTypeString == "write-only":
        return "SPIRIT_ACCESSTYPE_WRITEONLY"
    elif accessTypeString == "read-writeOnce":
        return "SPIRIT_ACCESSTYPE_READWRITEONCE"
    elif accessTypeString == "writeOnce":
        return "SPIRIT_ACCESSTYPE_WRITEONCE"
    else:
        return "NULL"


def convUsageTypeToDefine(usageType):
    if usageType == "memory":
        return "SPIRIT_USAGETYPE_MEMORY"
    elif usageType == "register":
        return "SPIRIT_USAGETYPE_REGISTER"
    elif usageType == "reserved":
        return "SPIRIT_USAGETYPE_RESERVED"
    else:
        return "NULL"

def convModifedWriteValueTypeToDefine(modifiedWriteValueType):
    if modifiedWriteValueType == "oneToClear":
        return "SPIRIT_MODIFIEDWRITEVALUETYPE_ONETOCLEAR"
    elif modifiedWriteValueType == "oneToSet":
        return "SPIRIT_MODIFIEDWRITEVALUETYPE_ONETOSET"
    elif modifiedWriteValueType == "oneToToggle":
        return "SPIRIT_MODIFIEDWRITEVALUETYPE_ONETOTOGGLE"
    elif modifiedWriteValueType == "zeroToClear":
        return "SPIRIT_MODIFIEDWRITEVALUETYPE_ZEROTOCLEAR"
    elif modifiedWriteValueType == "zeroToSet":
        return "SPIRIT_MODIFIEDWRITEVALUETYPE_ZEROTOSET"
    elif modifiedWriteValueType == "zeroToTogle":
        return "SPIRIt_MODIFIEDWRITEVALUETYPE_ZEROTOTOGGLE"
    elif modifiedWriteValueType == "clear":
        return "SPIRIT_MODIFIEDWRITEVALUETYPE_CLEAR"
    elif modifiedWriteValueType == "set":
        return "SPIRIT_MODIFIEDWRITEVALUETYPE_SET"
    elif modifiedWriteValueType == "modify":
        return "SPIRIT_MODIFIEDWRITEVALUETYPE_MODIFY"
    else:
        return "NULL"

def convReadActionTypeToDefine(readActionType):
    if readActionType == "clear": 
        return "SPIRIT_READACTIONTYPE_CLEAR" 
    if readActionType == "set": 
        return "SPIRIT_READACTIONTYPE_SET" 
    if readActionType == "modify": 
        return "SPIRIT_READACTIONTYPE_MODIFY" 
    else:
        return "NULL"    


    

def convTestConstraintTypeToDefine(testConstraintType):
    if testConstraintType == "unConstrained":
        return "SPIRIT_TESTCONSTRAINTTYPE_UNCONSTRAINED"
    elif testConstraintType == "restore":
        return "SPIRIT_TESTCONSTRAINTTYPE_RESTORE"
    elif testConstraintType == "writeAsRead":
        return "SPIRIT_TESTCONSTRAINTTYPE_WRITEASREAD"
    elif testConstraintType == "readOnly":
        return "SPIRIT_TESTCONSTRAINTTYPE_READONLY"
    else:
        return None
    
def convBool(boolString):
    if boolString.lower() == "false":
        return "SPIRIT_BOOL_FALSE"
    elif boolString.lower() == "true":
        return "SPIRIT_BOOL_TRUE"
    else:
        return None
    
def hasScaler(inStr):
    if getScalarFromString(inStr) == 1:
        return False
    else:
        return True

def isHex(inStr):
    if inStr[0:2] == '0x':
        return True
    else:
        return False
    
def getScaledInteger(inStr):
    if hasScaler(inStr):
        numStr = inStr[:-1]
        mult = getScalarFromString(inStr)
    else:
        numStr = inStr
        mult = 1
    
    if inStr[0] == '-':
        neg = -1
        numStr = numStr[1:]
    else:
        neg = 1
        
    try:
        if isHex(numStr):
            dec = int(numStr, 16)
        else:
            dec = int(numStr)
    except ValueError:
        raise Exception("Non std IPXACT integer \"%s\", see section C.9 of %s" % (inStr, C_LRM))
    
    return dec * mult * neg

def getScaledNonNegativeInteger(inStr):
    if inStr == None:
        return inStr
    
    num = getScaledInteger(inStr)
    
    if num < 0:
        raise Exception("Non negative number expected, received: %s" % (inStr))

    return num

def getScaledPositiveInteger(inStr):
    num = getScaledInteger(inStr)
    if num <= 0:
        raise Exception("Positive number expected, received: %s" % (inStr))

    return num

def getScalarFromString(scaledString):
    if scaledString[-1].upper() == 'K':
        multiplier = 2 ** 10
    elif scaledString[-1].upper() == 'M':
        multiplier = 2 ** 20
    elif scaledString[-1].upper() == 'G':
        multiplier = 2 ** 30
    elif scaledString[-1].upper() == 'T':
        multiplier = 2 ** 40 
    else:
        multiplier = 1 
    return multiplier

class formatEnum:
    hex = "hex"
    bin = "bin"
    dec = "dec"
    
def intToHexString(value, bits):
    if bits % 4 != 0:
        raise intToHexStringError("intToHexString: Cannot convert width %d to hex, only widths divisible of 4 allowed." % bits)
    return "{0:0{1}X}".format(value & ((1 << bits) - 1), bits // 4)

def intToBinString(value, bits):
    if math.ceil(math.log(value, 2)) > bits:
        raise intToBinStringError("intToBinString: bit width %d too small to represent value %d." % (bits, value))
    return "{0:0{1}b}".format(value & ((1 << bits) - 1), bits // 4)

def intToVhdlNumStr(num, width=32, formatIn=formatEnum.hex):
    if formatIn == formatEnum.hex:
        outStr = "X\"" + intToHexString(num, width) + "\""
    elif formatIn == formatEnum.dec:
        outStr = num
    elif formatIn == formatEnum.bin:
        outStr = intToBinString(num, 32)
    else:
        raise Exception("Integer format not supported")
    return outStr


def elementSort(elementList, xmlkey):
    # swap_test = False
    # getScaledNonNegativeInteger(addressBlockElementList[0].find(IPXACT_NS + 'baseAddress').text)
    for i in range(0, len(elementList) - 1):
        # as suggested by kubrick, makes sense
        swap_test = False
        for j in range(0, len(elementList) - i - 1):
            if getScaledNonNegativeInteger(ifNotNoneReturnText(elementList[j].find(xmlkey))) > getScaledNonNegativeInteger(ifNotNoneReturnText(elementList[j + 1].find(xmlkey))):
                elementList[j], elementList[j + 1] = elementList[j + 1], elementList[j]  # swap
            swap_test = True
        if swap_test == False:
            break

def getRegisterNum(thisRegisterElement):
    num = 0
    registerElementList = list()
    root = thisRegisterElement.find("../../../..")
    addressBlockElementList = getAddressBlockElementList(root)
    elementSort(addressBlockElementList, IPXACT_NS + 'baseAddress')
    for addressBlockElement in addressBlockElementList:
        registerElementList = addressBlockElement.findall(IPXACT_NS + "register")
        if addressBlockElement != thisRegisterElement.find("../."):
            num = num + len(registerElementList)
        else:
            elementSort(registerElementList, IPXACT_NS + 'addressOffset')
            for registerElement in registerElementList:
                if registerElement != thisRegisterElement:
                    num = num + 1
                else:
                    return num

def getPostfix(string, abbreviate):  
    if abbreviate:
        return C_POSTFIX[string]
    else:
        return string;


def getDesc(string, lang):
    if lang.upper() == "C":
        return """/*""" + C_DESC[string] + """*/"""
    elif lang.upper() == "VHDL":
        return "--" + C_DESC[string]
  
def getEnumStringsAsList(enumElement, conf):
    
    
    enumeratedValueList = enumElement.findall(IPXACT_NS + 'enumeratedValue')

    enumList = list()
        
    for enumeratedValue in enumeratedValueList:
        name = ifNotNoneReturnText(enumeratedValue.find(IPXACT_NS + 'name')) 
        value = ifNotNoneReturnText(enumeratedValue.find(IPXACT_NS + 'value')) 
        if name is not None and value is not None:
            enumList.append([name, ": integer", str(getScaledNonNegativeInteger(value))])
   
            
    return enumList
      
      


def getFieldStringsAsList(fieldElement, conf):
    name = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'name'))
    description = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'description'))
    bitOffset = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'bitOffset'))
    bitOffsetLow = bitOffset
    bitWidth = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'bitWidth'))
    bitOffsetHigh = str(getScaledInteger(bitOffsetLow) + getScaledInteger(bitWidth) - 1)
    volatile = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'volatile'))
    access = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'access'))
    modifiedWriteValue = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'modifiedWriteValue'))
    readAction = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'readAction'))
    testable = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'testable'))
    testConstraint = fieldElement.find(IPXACT_NS + 'testable').attrib[IPXACT_NS + 'testConstraint']

    fieldList = list()
    
    if conf.args.c:
        if name is not None:
            fieldList.append([getPostfix("NAME", conf.args.shortPostfix), "\"" + name + "\"", getDesc("NAME", "C")])
        if description is not None:
            fieldList.append([getPostfix("DESCRIPTION", conf.args.shortPostfix), "\"" + description + "\"", getDesc("DESCRIPTION", "C")])
        if bitOffset is not None:
            fieldList.append([getPostfix("BITOFFSET", conf.args.shortPostfix), bitOffset, getDesc("BITOFFSET", "C")])
        if bitWidth is not None:
            fieldList.append([getPostfix("BITWIDTH", conf.args.shortPostfix), bitWidth, getDesc("BITWIDTH", "C")])
        if volatile is not None:
            fieldList.append([getPostfix("VOLATILE", conf.args.shortPostfix), convBool(volatile), getDesc("VOLATILE", "C")])
        if access is not None:
            fieldList.append([getPostfix("ACCESS", conf.args.shortPostfix), convAccessTypeToDefine(access), getDesc("ACCESS", "C")])
        if modifiedWriteValue is not None:
            fieldList.append([getPostfix("MODIFIEDWRITEVALUE", conf.args.shortPostfix), convModifedWriteValueTypeToDefine(modifiedWriteValue), getDesc("MODIFIEDWRITEVALUE", "C")])
        if readAction is not None:
            fieldList.append([getPostfix("READACTION", conf.args.shortPostfix), convReadActionTypeToDefine(readAction), getDesc("READACTION", "C")])    
        if testable is not None:
            fieldList.append([getPostfix("TESTABLE", conf.args.shortPostfix), convBool(testable), getDesc("TESTABLE", "C")])    
        if testConstraint is not None:
            fieldList.append([getPostfix("TESTCONSTRAINT", conf.args.shortPostfix), convTestConstraintTypeToDefine(testConstraint), getDesc("TESTCONSTRAINT", "C")])    
    elif conf.args.vhdl: 
        if name is not None:
            fieldList.append([getPostfix("NAME", conf.args.shortPostfix), ": string", "\"" + name + "\""])
        if description is not None:
            fieldList.append([getPostfix("DESCRIPTION", conf.args.shortPostfix), ": string", "\"" + description + "\""])
        if bitOffset is not None:
            fieldList.append([getPostfix("BITOFFSET", conf.args.shortPostfix), ": integer", bitOffset])
        if bitOffsetLow is not None:
            fieldList.append([getPostfix("BITOFFSETLOW", conf.args.shortPostfix), ": integer", bitOffsetLow])
        if bitOffsetHigh is not None:
            fieldList.append([getPostfix("BITOFFSETHIGH", conf.args.shortPostfix), ": integer", bitOffsetHigh])
        if bitWidth is not None:
            fieldList.append([getPostfix("BITWIDTH", conf.args.shortPostfix), ": integer", bitWidth])
        if volatile is not None:
            fieldList.append([getPostfix("VOLATILE", conf.args.shortPostfix), ": spiritBoolType", convBool(volatile)])
        if access is not None:
            fieldList.append([getPostfix("ACCESS", conf.args.shortPostfix), ": spiritAccessType", convAccessTypeToDefine(access)])
        if modifiedWriteValue is not None:
            fieldList.append([getPostfix("MODIFIEDWRITEVALUE", conf.args.shortPostfix), ": spiritModifiedWriteValueType", convModifedWriteValueTypeToDefine(modifiedWriteValue) ])
        if readAction is not None:
            fieldList.append([getPostfix("READACTION", conf.args.shortPostfix), ": spiritReadActionType", convReadActionTypeToDefine(readAction)])    
        if testable is not None:
            fieldList.append([getPostfix("TESTABLE", conf.args.shortPostfix), ": spiritBoolType", convBool(testable)])    
        if testConstraint is not None:
            fieldList.append([getPostfix("TESTCONSTRAINT", conf.args.shortPostfix), ": spiritTestconstraintType", convTestConstraintTypeToDefine(testConstraint)])    
            
    return fieldList





def getRegisterStringsAsList(registerElement, conf):
    name = ifNotNoneReturnText(registerElement.find(IPXACT_NS + 'name'))
    description = ifNotNoneReturnText(registerElement.find(IPXACT_NS + 'description'))
    dim = ifNotNoneReturnText(registerElement.find(IPXACT_NS + 'dim'))
    addressOffset = ifNotNoneReturnText(registerElement.find(IPXACT_NS + 'addressOffset'))
    baseAddress = ifNotNoneReturnText(registerElement.find("../" + IPXACT_NS + "baseAddress"))
    size = ifNotNoneReturnText(registerElement.find(IPXACT_NS + 'size'))
    volatile = ifNotNoneReturnText(registerElement.find(IPXACT_NS + 'volatile'))
    access = ifNotNoneReturnText(registerElement.find(IPXACT_NS + 'access'))
    resetValue = ifNotNoneReturnText(registerElement.find(IPXACT_NS + 'reset/' + IPXACT_NS + 'value'))
    resetMask = ifNotNoneReturnText(registerElement.find(IPXACT_NS + 'reset/' + IPXACT_NS + 'mask'))
    number = getRegisterNum(registerElement)
                            
    regList = list()
    if conf.args.c:
        if name is not None:
            regList.append([getPostfix("NAME", conf.args.shortPostfix), "\"" + name + "\"", getDesc("NAME", "C")])
        if description is not None:
            regList.append([getPostfix("DESCRIPTION", conf.args.shortPostfix), "\"" + description + "\"", getDesc("DESCRIPTION", "C")])
        if dim is not None:
            regList.append([getPostfix("DIM", conf.args.shortPostfix), dim, getDesc("DIM", "C")])
        if addressOffset is not None:
            regList.append([getPostfix("ADDRESSBLOCKOFFSET", conf.args.shortPostfix), addressOffset, getDesc("ADDRESSBLOCKOFFSET", "C")])
        if addressOffset and baseAddress is not None:
            regList.append([getPostfix("BASEADDRESSOFFSET", conf.args.shortPostfix), hex(getScaledNonNegativeInteger(addressOffset) + getScaledNonNegativeInteger(baseAddress)), getDesc("BASEADDRESSOFFSET", "C")])
        if size is not None:
            regList.append([getPostfix("SIZE", conf.args.shortPostfix), size, getDesc("SIZE", "C")])
        if volatile is not None:
            regList.append([getPostfix("VOLATILE", conf.args.shortPostfix), convBool(volatile), getDesc("VOLATILE", "C")])
        if access is not None:
            regList.append([getPostfix("ACCESS", conf.args.shortPostfix), convAccessTypeToDefine(access), getDesc("ACCESS", "C")])
        if resetValue is not None:
            regList.append([getPostfix("RESETVALUE", conf.args.shortPostfix), resetValue, getDesc("RESETVALUE", "C")])    
        if resetMask is not None:
            regList.append([getPostfix("RESETMASK", conf.args.shortPostfix), resetMask, getDesc("RESETMASK", "C")])  
    elif conf.args.vhdl: 
        if name is not None:
            regList.append([getPostfix("NAME", conf.args.shortPostfix), ": string", "\"" + name + "\""])
        if description is not None:
            regList.append([getPostfix("DESCRIPTION", conf.args.shortPostfix), ": string", "\"" + description + "\""])
        if dim is not None:
            regList.append([getPostfix("DIM", conf.args.shortPostfix), ": integer", dim])
        if addressOffset is not None:
            regList.append([getPostfix("ADDRESSBLOCKOFFSET", conf.args.shortPostfix), ": std_logic_vector(" + str(conf.args.regAddressOffsetWidth - 1) + " downto 0)", intToVhdlNumStr(getScaledNonNegativeInteger(addressOffset), conf.args.regAddressOffsetWidth, conf.args.regAddressOffsetFormat)])
        if addressOffset and baseAddress is not None:
            regList.append([getPostfix("BASEADDRESSOFFSET", conf.args.shortPostfix), ": std_logic_vector(" + str(conf.args.regBaseAddressOffsetWidth - 1) + " downto 0)", intToVhdlNumStr(getScaledNonNegativeInteger(addressOffset) + getScaledNonNegativeInteger(baseAddress), conf.args.regBaseAddressOffsetWidth, conf.args.regBaseAddressOffsetFormat)])
        if size is not None:
            regList.append([getPostfix("SIZE", conf.args.shortPostfix), ": integer", size])
        if volatile is not None:
            regList.append([getPostfix("VOLATILE", conf.args.shortPostfix), ": spiritBoolType", convBool(volatile)])
        if access is not None:
            regList.append([getPostfix("ACCESS", conf.args.shortPostfix), ": spiritAccessType", convAccessTypeToDefine(access)])
        if resetValue is not None:
            regList.append([getPostfix("RESETVALUE", conf.args.shortPostfix), ": std_logic_vector(" + str(conf.args.regResetValueWidth - 1) + " downto 0)", intToVhdlNumStr(getScaledNonNegativeInteger(resetValue), conf.args.regResetValueWidth, conf.args.regResetValueFormat)]) 
        if resetMask is not None:
            regList.append([getPostfix("RESETMASK", conf.args.shortPostfix), ": std_logic_vector(" + str(conf.args.regResetMaskWidth - 1) + " downto 0)", intToVhdlNumStr(getScaledNonNegativeInteger(resetMask), conf.args.regResetMaskWidth, conf.args.regResetMaskFormat)])
        if number is not None:
            regList.append([getPostfix("NUMBER", conf.args.shortPostfix), ": integer", str(number)])
    return regList


def getAddressBlockStringsAsList(addressBlockElement, conf):
    name = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'name'))
    usage = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'usage'))
    baseAddress = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'baseAddress'))
    highAddress = hex(getScaledNonNegativeInteger(ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'baseAddress'))) + 
                      getScaledNonNegativeInteger(ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'range'))) - 1)
    _range = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'range'))
    width = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'width'))
    description = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'description'))
    access = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'access'))
    volatile = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'volatile'))
    modifiedWriteValue = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'modifiedWriteValue'))
    readAction = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'readAction'))
    testable = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'testable'))
    numberOfRegs = len(addressBlockElement.findall(IPXACT_NS + "register"))
    
    
  
    abList = list()
    if conf.args.c:
        if name is not None:
            abList.append([getPostfix("NAME", conf.args.shortPostfix), "\"" + name + "\"", getDesc("NAME", "C")])
        if usage is not None:
            abList.append([getPostfix("USAGE", conf.args.shortPostfix), "\"" + usage + "\"", getDesc("USAGE", "C")])
        if baseAddress is not None:
            abList.append([getPostfix("BASEADDRESS", conf.args.shortPostfix), baseAddress, getDesc("BASEADDRESS", "C")])
        if highAddress is not None:
            abList.append([getPostfix("HIGHADDRESS", conf.args.shortPostfix), highAddress, getDesc("HIGHADDRESS", "C")])
        if range is not None:
            abList.append([getPostfix("RANGE", conf.args.shortPostfix), _range, getDesc("RANGE", "C")])
        if width is not None:
            abList.append([getPostfix("WIDTH", conf.args.shortPostfix), width, getDesc("WIDTH", "C")])
        if description is not None:
            abList.append([getPostfix("DESCRIPTION", conf.args.shortPostfix), "\"" + description + "\"", getDesc("DESCRIPTION", "C")])
        if access is not None:
            abList.append([getPostfix("ACCESS", conf.args.shortPostfix), convAccessTypeToDefine(access), getDesc("ACCESS", "C")])
        if volatile is not None:
            abList.append([getPostfix("VOLATILE", conf.args.shortPostfix), convBool(volatile), getDesc("VOLATILE", "C")])
        if modifiedWriteValue is not None:
            abList.append([getPostfix("MODIFIEDWRITEVALUE", conf.args.shortPostfix), convModifedWriteValueTypeToDefine(modifiedWriteValue), getDesc("MODIFIEDWRITEVALUE", "C")])
        if readAction is not None:
            abList.append([getPostfix("READACTION", conf.args.shortPostfix), convReadActionTypeToDefine(readAction), getDesc("READACTION", "C")])
        if testable is not None:
            abList.append([getPostfix("TESTABLE", conf.args.shortPostfix), convBool(testable), getDesc("TESTABLE", "C")])
            
    elif conf.args.vhdl: 
        if name is not None:
            abList.append([getPostfix("NAME", conf.args.shortPostfix), ": string", "\"" + name + "\"", getDesc("NAME", "VHDL")])
        if usage is not None:
            abList.append([getPostfix("USAGE", conf.args.shortPostfix), ": string", "\"" + usage + "\"", getDesc("NAME", "VHDL")])
        if baseAddress is not None:
            abList.append([getPostfix("BASEADDRESS", conf.args.shortPostfix), ": std_logic_vector(" + str(conf.args.abBaseAddressWidth - 1) + " downto 0)", intToVhdlNumStr(getScaledNonNegativeInteger(baseAddress), conf.args.abBaseAddressWidth, conf.args.abBaseAddressFormat), getDesc("NAME", "VHDL")])
        if highAddress is not None:
            abList.append([getPostfix("HIGHADDRESS", conf.args.shortPostfix), ": std_logic_vector(" + str(conf.args.abHighAddressWidth - 1) + " downto 0)", intToVhdlNumStr(getScaledNonNegativeInteger(highAddress), conf.args.abHighAddressWidth, conf.args.abHighAddressFormat), getDesc("NAME", "VHDL")])
        if range is not None:
            abList.append([getPostfix("RANGE", conf.args.shortPostfix), ": integer", _range, getDesc("NAME", "VHDL")])
        if width is not None:
            abList.append([getPostfix("WIDTH", conf.args.shortPostfix), ": integer", width, getDesc("NAME", "VHDL")])
        if description is not None:
            abList.append([getPostfix("DESCRIPTION", conf.args.shortPostfix), ": string", "\"" + description + "\"", getDesc("NAME", "VHDL")])
        if access is not None:
            abList.append([getPostfix("ACCESS", conf.args.shortPostfix), ": spiritAccessType", convAccessTypeToDefine(access), getDesc("NAME", "VHDL")])
        if volatile is not None:
            abList.append([getPostfix("VOLATILE", conf.args.shortPostfix), ": spiritBoolType", convBool(volatile), getDesc("NAME", "VHDL")])
        if modifiedWriteValue is not None:
            abList.append([getPostfix("MODIFIEDWRITEVALUE", conf.args.shortPostfix), ": spiritModifiedWriteValueType", convModifedWriteValueTypeToDefine(modifiedWriteValue), getDesc("NAME", "VHDL")])
        if readAction is not None:
            abList.append([getPostfix("READACTION", conf.args.shortPostfix), ": spiritReadActionType", convReadActionTypeToDefine(readAction), getDesc("NAME", "VHDL")])
        if testable is not None:
            abList.append([getPostfix("TESTABLE", conf.args.shortPostfix), ": spiritBoolType", convBool(testable), getDesc("NAME", "VHDL")]) 
        if numberOfRegs is not None:
            abList.append([getPostfix("NUMBEROFREGS", conf.args.shortPostfix), ": integer", str(numberOfRegs), getDesc("NAME", "VHDL")])
        
    return abList;
  
  

def abPrint(root, conf):
    addressBlockElementList = getAddressBlockElementList(root)
    
    printStr = ""

    for addressBlockElement in addressBlockElementList:
        abStringsList = getAddressBlockStringsAsList(addressBlockElement, conf)
        abColumnMaxLengths = getMaxLengtOfColumnsAsList(abStringsList)
        compName = ifNotNoneReturnText(root.find('./' + IPXACT_NS + 'name'))
        abName = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'name'))
        
        if conf.args.vhdl:
            printStr += "\n\n-- Addressblock " + abName + " --"
            formatStr = "constant "
            if not conf.args.noComponentNameInAb:
                formatStr += compName.upper() + "_"
            formatStr += "{0}_{{{1}}} {{{2}}} := {{{3}}};".format(abName.upper(), "0:<" + str(abColumnMaxLengths[0]), "1:<" + str(abColumnMaxLengths[1]), "2:<")
        elif conf.args.c:
            printStr += "\n\n/* Addressblock " + abName + " */"
            formatStr = "#define {0}_{1}_{{{2}}}\t{{{3}}}\t{{{4}}}".format(compName.upper(), abName.upper(), "0:<" + str(abColumnMaxLengths[0]), "1:<" + str(abColumnMaxLengths[1]), "2:<" + str(abColumnMaxLengths[2]))
        
        
        for abStrings in abStringsList:
            if conf.args.vhdl:
                printStr += "\n" + formatStr.format(abStrings[0], abStrings[1], abStrings[2])
            elif conf.args.c:
                printStr += "\n" + formatStr.format(abStrings[0], abStrings[1], abStrings[2])
            
    return printStr

def regPrint(root, conf):
    registerElementList = getRegisterElementList(root)
    
    printStr = ""
    
    for registerElement in registerElementList:
        regStringsList = getRegisterStringsAsList(registerElement, conf)
        regColumnMaxLengths = getMaxLengtOfColumnsAsList(regStringsList)
        compName = ifNotNoneReturnText(root.find('./' + IPXACT_NS + 'name'))
        abName = ifNotNoneReturnText(registerElement.find("../%sname" % IPXACT_NS))
        regName = ifNotNoneReturnText(registerElement.find(IPXACT_NS + 'name'))
        if conf.args.vhdl:
            printStr += "\n\n-- Register " + regName + " --"
            formatStr = "constant "
            if not conf.args.noComponentNameInReg:
                formatStr += compName.upper() + "_"
            if not conf.args.noAddressBlockNameInReg:
                formatStr += abName.upper() + "_"   
            formatStr += "{0}_{{{1}}} {{{2}}} := {{{3}}};".format(regName.upper(), "0:<" + str(regColumnMaxLengths[0]), "1:<" + str(regColumnMaxLengths[1]), "2:<")
        elif conf.args.c:
            printStr += "\n\n/* Register " + regName + " */"
            formatStr = "#define {0}_{1}_{2}_{{{3}}}\t{{{4}}}\t{{{5}}}".format(compName.upper(), abName.upper(), regName.upper(), "0:<" + str(regColumnMaxLengths[0]), "1:<" + str(regColumnMaxLengths[1]), "2:<" + str(regColumnMaxLengths[2]))
                  
        for regStrings in regStringsList:
            if conf.args.vhdl:
                printStr += "\n" + formatStr.format(regStrings[0], regStrings[1], regStrings[2])
            elif conf.args.c:
                printStr += "\n" + formatStr.format(regStrings[0], regStrings[1], regStrings[2])
            
    return printStr

def enumsPrint(root, conf):
    enumElementList = getEnumElementList(root)
    
    printStr = ""
    
    for enumElement in enumElementList:
        enumStringsList = getEnumStringsAsList(enumElement, conf)
        enumColumnMaxLengths = getMaxLengtOfColumnsAsList(enumStringsList)
#       compName = ifNotNoneReturnText(root.find('./' + IPXACT_NS + 'name'))
        abName = ifNotNoneReturnText(enumElement.find("../../../%sname" % IPXACT_NS))
        regName = ifNotNoneReturnText(enumElement.find("../../%sname" % IPXACT_NS))
        fieldName = ifNotNoneReturnText(enumElement.find("../%sname" % IPXACT_NS))
        
        if conf.args.vhdl:
            formatStr = "constant "
            if not conf.args.noAddressBlockNameInField:
                formatStr += abName.upper() + "_"
            if not conf.args.noRegisterNameInField:
                formatStr += regName.upper() + "_" 
            formatStr += "{0}_{{{1}}} {{{2}}} := {{{3}}};".format(fieldName.upper(), "0:<" + str(enumColumnMaxLengths[0]), "1:<" + str(enumColumnMaxLengths[1]), "2:<")
        elif conf.args.c:
            formatStr = "\t {0}_{1}_{2}_{3} = {4}"
            
            
    
        if conf.args.vhdl:
            printStr += "\n\n-- enum " + fieldName + " --"
            for enumStrings in enumStringsList:
                printStr += "\n" + formatStr.format(enumStrings[0].upper(), enumStrings[1], enumStrings[2])
        elif conf.args.c:
            printStr += "\n\n/* enum " + fieldName + " */"
            printStr += "\n typedef enum {\n"
            for enumStrings in enumStringsList:
                printStr += formatStr.format(abName.upper(), regName.upper(), fieldName.upper(), enumStrings[0].upper(), enumStrings[1])
                if enumStrings != enumStringsList[-1]:
                    printStr += ","
                printStr += "\n"      
            printStr += "} " + "{0}_{1}_{2}_ENUM;".format(abName.upper(), regName.upper(), fieldName.upper())
            
    return printStr

def fieldsPrint(root, conf):
    fieldElementList = getFieldElementList(root)
    
    printStr = ""
    
    for fieldElement in fieldElementList:
        fieldStringsList = getFieldStringsAsList(fieldElement, conf)
        fieldColumnMaxLengths = getMaxLengtOfColumnsAsList(fieldStringsList)
        compName = ifNotNoneReturnText(root.find('./' + IPXACT_NS + 'name'))
        abName = ifNotNoneReturnText(fieldElement.find("../../%sname" % IPXACT_NS))
        regName = ifNotNoneReturnText(fieldElement.find("../%sname" % IPXACT_NS))
        fieldName = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'name'))
        if conf.args.vhdl:
            printStr += "\n\n-- Field " + fieldName + " --"
            formatStr = "constant "
            if not conf.args.noComponentNameInField:
                formatStr += compName.upper() + "_"
            if not conf.args.noAddressBlockNameInField:
                formatStr += abName.upper() + "_"
            if not conf.args.noRegisterNameInField:
                formatStr += regName.upper() + "_" 
            formatStr += "{0}_{{{1}}} {{{2}}} := {{{3}}};".format(fieldName.upper(), "0:<" + str(fieldColumnMaxLengths[0]), "1:<" + str(fieldColumnMaxLengths[1]), "2:<")
        elif conf.args.c:
            printStr += "\n\n/* Field " + fieldName + " */"
            formatStr = "#define {0}_{1}_{2}_{3}_{{{4}}}\t{{{5}}}\t{{{6}}}".format(compName.upper(), abName.upper(), regName.upper(), fieldName.upper(), "0:<" + str(fieldColumnMaxLengths[0]), "1:<" + str(fieldColumnMaxLengths[1]), "2:<" + str(fieldColumnMaxLengths[2]))
    
        for fieldStrings in fieldStringsList:
            if conf.args.vhdl:
                printStr += "\n" + formatStr.format(fieldStrings[0], fieldStrings[1], fieldStrings[2])
            elif conf.args.c:
                printStr += "\n" + formatStr.format(fieldStrings[0], fieldStrings[1], fieldStrings[2])
            
    return printStr
                    
            
class Config():
    def __init__(self, args):
        self.args = args
    
    


def vhdlFilePrint(root, conf):
    vhdlConf = conf
    vhdlConf.c = None
    printStr = ''
    printStr += VHDL_HEADER
    printStr += VHDL_SPIRIT_TYPES
    printStr += abPrint(root, vhdlConf)
    printStr += regPrint(root, vhdlConf)
    printStr += fieldsPrint(root, vhdlConf)
    printStr += enumsPrint(root, vhdlConf)
    printStr += VHDL_FOOTER
        
    return printStr
    
            
            
def cFilePrint(root, conf):
    cConf = conf
    cConf.vhdl = None
    printStr = ''
    printStr += C_PRAGMA_ONCE
    printStr += C_SPIRIT_TYPES
    printStr += abPrint(root, cConf)
    printStr += regPrint(root, cConf)
    printStr += fieldsPrint(root, cConf)
    printStr += enumsPrint(root, cConf)
    
    return printStr


def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''
    
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

Created by Klaus Petersen on %s.
This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2.

http://www.wtfpl.net/txt/copying/

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument(dest="inpath", help="path to input IP-XACT source file")
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument('-c', action='store_true', help="enable c header output")
        parser.add_argument('-vhdl', action='store_true', help="enable vhdl package output")
        parser.add_argument('-shortPostfix', action='store_true', help="Abbreviate postfix, i.e _DESCRIPTION -> _DESC")
        parser.add_argument('-noComponentNameInAb', action='store_true', help="Exclude component name from generated address block names. Warning: This could cause naming conflicts.")
        parser.add_argument('-noComponentNameInReg', action='store_true', help="Exclude component name from generated register names. Warning: This could cause naming conflicts.")
        parser.add_argument('-noAddressBlockNameInReg', action='store_true', help="Exclude address block name from generated register names. Warning: This could cause naming conflicts.")
        parser.add_argument('-noComponentNameInField', action='store_true', help="Exclude component name from generated field names. Warning: This could cause naming conflicts.")
        parser.add_argument('-noAddressBlockNameInField', action='store_true', help="Exclude address block name from generated field names. Warning: This could cause naming conflicts.")
        parser.add_argument('-noRegisterNameInField', action='store_true', help="Exclude register name from generated field names. Warning: This could cause naming conflicts.")
        parser.add_argument('-abBaseAddressWidth', help="width of std_logic_vector in generated addressblock address output [default: %(default)s]", metavar='width', default=64, type=int)
        parser.add_argument('-abBaseAddressFormat', help="format of std_logic_vector in generated addressblock address output [default: %(default)s]", metavar='format', default="hex")
        parser.add_argument('-abHighAddressWidth', help="width of std_logic_vector in generated addressblock address output [default: %(default)s]", metavar='width', default=64, type=int)
        parser.add_argument('-abHighAddressFormat', help="format of std_logic_vector in generated addressblock address output [default: %(default)s]", metavar='format', default="hex")
        parser.add_argument('-regAddressOffsetWidth', help="width of std_logic_vector in generated register address offset output [default: %(default)s]", metavar='width', default=32, type=int)
        parser.add_argument('-regAddressOffsetFormat', help="format of std_logic_vector in generated register address offset output [default: %(default)s]", metavar='format', default="hex")
        parser.add_argument('-regResetMaskWidth', help="width of std_logic_vector in generated register reset mask output [default: %(default)s]", metavar='width', default=64, type=int)
        parser.add_argument('-regResetMaskFormat', help="format of std_logic_vector in generated register reset mask output [default: %(default)s]", metavar='format', default="hex")
        parser.add_argument('-regResetValueWidth', help="width of std_logic_vector in generated register reset value output [default: %(default)s]", metavar='width', default=32, type=int)
        parser.add_argument('-regResetValueFormat', help="format of std_logic_vector in generated register reset value output [default: %(default)s]", metavar='format', default="hex")
        parser.add_argument('-regBaseAddressOffsetWidth', help="width of std_logic_vector in generated register address offset output [default: %(default)s]", metavar='width', default=32, type=int)
        parser.add_argument('-regBaseAddressOffsetFormat', help="format of std_logic_vector in generated register address offset mask output [default: %(default)s]", metavar='format', default="hex")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-cpath', dest="outc", help="Output path for c header file [default: %(default)s]",  default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "out/ipxact.h"))
        parser.add_argument('-vhdlpath', dest="outvhdl", help="Ouput path for vhdl package file [default: %(default)s]",  default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "out/ipxact.vhd"))
        
        # Process arguments
        args = parser.parse_args()
  
        if args.verbose:
            log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG, stream=sys.stdout)
        else:
            log.basicConfig(format="%(levelname)s: %(message)s")
                  
        if args.inpath is not None:
            inpath = os.path.normpath(args.inpath)
        
        if args.outvhdl is not None:
            args.outvhdl = os.path.abspath(os.path.normpath(args.outvhdl))
            
        if args.outc is not None:
            args.outc = os.path.abspath(os.path.normpath(args.outc))
    
        log.info("Input path: %s" % inpath)
            
        
        conf = Config(args)
            
        try:
            root = openXMLFileReturnRoot(inpath)
            
            if args.vhdl:
                log.info("Out directory (VHDL paclage): %s" % args.outvhdl)
                printStr = vhdlFilePrint(root, conf)
                if not os.path.exists(os.path.dirname(args.outvhdl)):
                    os.makedirs(os.path.dirname(args.outvhdl))
                with open(args.outvhdl, "w") as f:
                    f.write(printStr)
                    log.info("Wrote vhdl package to %s" % args.outvhdl)
        
        
            if args.c:
                log.info("Out directory (C header): %s" % args.outc)
                printStr = cFilePrint(root, conf)
                if not os.path.exists(os.path.dirname(args.outc)):
                    os.makedirs(os.path.dirname(args.outc))
                with open(args.outc, "w") as f:
                    f.write(printStr)
                    log.info("Wrote c header to %s" % args.outc)
                
        except IOError as (errno, strerror):
            log.error("I/O error({0}): {1}".format(errno, strerror))
             
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2
    except SystemExit:
        log.info("End of program")
    except :
        log.error("Unexpected error:", sys.exc_info()[0])

if __name__ == "__main__":
    if DEBUG:
        # sys.argv.append("-h")
        sys.argv.append("-v")
        # sys.argv.append("-V")
        pass
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'ipxact_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())    
    

