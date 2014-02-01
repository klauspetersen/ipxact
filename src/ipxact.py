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
#typedef enum{
    SPIRIT_ACCESSTYPE_READWRITE,
    SPIRIT_ACCESSTYPE_READONLY,
    SPIRIT_ACCESSTYPE_WRITEONLY,
    SPIRIT_ACCESSTYPE_READWRITEONCE,
    SPIRIT_ACCESSTYPE_WRITEONCE
}SPIRIT_ACCESSTYPE_T;

#typedef enum{
    SPIRIT_USAGETYPE_MEMORY, 
    SPIRIT_USAGETYPE_REGISTER,
    SPIRIT_USAGETYPE_RESERVED
} SPIRIT_USAGETYPE_T;

#typedef enum{
    SPIRIT_TESTCONSTRAINTTYPE_UNCONSTRAINED,
    SPIRIT_TESTCONSTRAINTTYPE_RESTORE,
    SPIRIT_TESTCONSTRAINTTYPE_WRITEASREAD,
    SPIRIT_TESTCONSTRAINTTYPE_READONLY
} SPIRIT_TESTCONSTRAINTTYPE_T;

#typedef enum{
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

#typedef enum{
    SPIRIT_READACTIONTYPE_CLEAR,
    SPIRIT_READACTIONTYPE_SET,
    SPIRIT_READACTIONTYPE_MODIFY
} SPIRIT_READACTIONTYPE_T;

#typedef enum{
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
        
VHDL_HEADER ='''
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
        raise Exception("Non std IPXACT integer \"%s\", see section C.9 of %s" %(inStr, C_LRM))
    
    return dec * mult * neg

def getScaledNonNegativeInteger(inStr):
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
        multiplier = 2**10
    elif scaledString[-1].upper() == 'M':
        multiplier = 2**20
    elif scaledString[-1].upper() == 'G':
        multiplier = 2**30
    elif scaledString[-1].upper() == 'T':
        multiplier = 2**40 
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
    return "{0:0{1}X}".format(value & ((1<<bits) - 1), bits//4)

def intToBinString(value, bits):
    if math.ceil(math.log(value, 2)) > bits:
        raise intToBinStringError("intToBinString: bit width %d too small to represent value %d." %(bits, value))
    return "{0:0{1}b}".format(value & ((1<<bits) - 1), bits//4)

def intToVhdlNumStr(num, width = 32, formatIn = formatEnum.hex):
    if formatIn == formatEnum.hex:
        outStr = "X\"" + intToHexString(num, width) + "\""
    elif formatIn == formatEnum.dec:
        outStr = num
    elif formatIn == formatEnum.bin:
        outStr = intToBinString(num, 32)
    else:
        raise Exception("Integer format not supported")
    return outStr
    

def getFieldStringsAsList(fieldElement, ipxactConfig):
    name = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'name'))
    description = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'description'))
    bitOffset = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'bitOffset'))
    bitWidth = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'bitWidth'))
    volatile = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'volatile'))
    access = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'access'))
    modifiedWriteValue = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'modifiedWriteValue'))
    readAction = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'readAction'))
    testable = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'testable'))
    testConstraint = fieldElement.find(IPXACT_NS + 'testable').attrib[IPXACT_NS + 'testConstraint']

    fieldList = list()
    
    if ipxactConfig.output == outputType.c:
        if name is not None:
            fieldList.append(["NAME", "\"" + name + "\""])
        if description is not None:
            fieldList.append(["DESCRIPTION", "\"" + description + "\""])
        if bitOffset is not None:
            fieldList.append(["BITOFFSET", bitOffset])
        if bitWidth is not None:
            fieldList.append(["BITWIDTH", bitWidth])
        if volatile is not None:
            fieldList.append(["VOLATILE", convBool(volatile)])
        if access is not None:
            fieldList.append(["ACCESS", convAccessTypeToDefine(access)])
        if modifiedWriteValue is not None:
            fieldList.append(["MODIFIEDWRITEVALUE", convModifedWriteValueTypeToDefine(modifiedWriteValue) ])
        if readAction is not None:
            fieldList.append(["READACTION", convReadActionTypeToDefine(readAction)])    
        if testable is not None:
            fieldList.append(["TESTABLE", convBool(testable)])    
        if testConstraint is not None:
            fieldList.append(["TESTCONSTRAINT", convTestConstraintTypeToDefine(testConstraint)])    
    elif ipxactConfig.output == outputType.vhdl: 
        if name is not None:
            fieldList.append(["NAME", ": string", "\"" + name + "\""])
        if description is not None:
            fieldList.append(["DESCRIPTION", ": string", "\"" + description + "\""])
        if bitOffset is not None:
            fieldList.append(["BITOFFSET", ": integer", bitOffset])
        if bitWidth is not None:
            fieldList.append(["BITWIDTH", ": integer", bitWidth])
        if volatile is not None:
            fieldList.append(["VOLATILE", ": boolean", convBool(volatile)])
        if access is not None:
            fieldList.append(["ACCESS", ": spiritAccessType", convAccessTypeToDefine(access)])
        if modifiedWriteValue is not None:
            fieldList.append(["MODIFIEDWRITEVALUE", ": spiritModifiedWriteValueType",  convModifedWriteValueTypeToDefine(modifiedWriteValue) ])
        if readAction is not None:
            fieldList.append(["READACTION", ": spiritReadActionType", convReadActionTypeToDefine(readAction)])    
        if testable is not None:
            fieldList.append(["TESTABLE", ": boolean",  convBool(testable)])    
        if testConstraint is not None:
            fieldList.append(["TESTCONSTRAINT", ": spiritTestconstraintType",  convTestConstraintTypeToDefine(testConstraint)])    
            
    return fieldList





def getRegisterStringsAsList(registerElement, ipxactConfig):
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
                            
    regList = list()
    if ipxactConfig.output == outputType.c:
        if name is not None:
            regList.append(["NAME", "\"" + name + "\""])
        if description is not None:
            regList.append(["DESCRIPTION", "\"" + description + "\""])
        if dim is not None:
            regList.append(["DIM", dim])
        if addressOffset is not None:
            regList.append(["ADDRESSBLOCKOFFSET", addressOffset])
        if addressOffset and baseAddress is not None:
            regList.append(["BASEADDRESSOFFSET", hex(getScaledNonNegativeInteger(addressOffset) + getScaledNonNegativeInteger(baseAddress))])
        if size is not None:
            regList.append(["SIZE", size])
        if volatile is not None:
            regList.append(["VOLATILE", convBool(volatile)])
        if access is not None:
            regList.append(["ACCESS", convAccessTypeToDefine(access)])
        if resetValue is not None:
            regList.append(["RESETVALUE", resetValue])    
        if resetMask is not None:
            regList.append(["RESETMASK", resetMask])  
    elif ipxactConfig.output == outputType.vhdl: 
        if name is not None:
            regList.append(["NAME", ": string", "\"" + name + "\""])
        if description is not None:
            regList.append(["DESCRIPTION", ": string", "\"" + description + "\""])
        if dim is not None:
            regList.append(["DIM", ": integer", dim])
        if addressOffset is not None:
            regList.append(["ADDRESSBLOCKOFFSET", ": std_logic_vector(" + str(ipxactConfig.regAddressOffsetWidth-1) + " downto 0)", intToVhdlNumStr(getScaledNonNegativeInteger(addressOffset), ipxactConfig.regAddressOffsetWidth, ipxactConfig.regAddressOffsetFormat)])
        if addressOffset and baseAddress is not None:
            regList.append(["BASEADDRESSOFFSET", ": std_logic_vector(" + str(ipxactConfig.regBaseAddressOffsetWidth-1) + " downto 0)", intToVhdlNumStr(getScaledNonNegativeInteger(addressOffset) + getScaledNonNegativeInteger(baseAddress), ipxactConfig.regBaseAddressOffsetWidth, ipxactConfig.regBaseAddressOffsetFormat)])
        if size is not None:
            regList.append(["SIZE", ": integer", size])
        if volatile is not None:
            regList.append(["VOLATILE", ": boolean", convBool(volatile)])
        if access is not None:
            regList.append(["ACCESS", ": spiritAccessType", convAccessTypeToDefine(access)])
        if resetValue is not None:
            regList.append(["RESETVALUE", ": std_logic_vector(" + str(ipxactConfig.regResetValueWidth-1) + " downto 0)", intToVhdlNumStr(getScaledNonNegativeInteger(resetValue), ipxactConfig.regResetValueWidth, ipxactConfig.regResetValueFormat)]) 
        if resetMask is not None:
            regList.append(["RESETMASK", ": std_logic_vector(" + str(ipxactConfig.regResetMaskWidth-1) + " downto 0)", intToVhdlNumStr(getScaledNonNegativeInteger(resetMask), ipxactConfig.regResetMaskWidth, ipxactConfig.regResetMaskFormat)])
    return regList


def getAddressBlockStringsAsList(addressBlockElement, ipxactConfig):
    name = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'name'))
    usage = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'usage'))
    baseAddress = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'baseAddress'))
    _range = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'range'))
    width = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'width'))
    description = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'description'))
    access = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'access'))
    volatile = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'volatile'))
    modifiedWriteValue = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'modifiedWriteValue'))
    readAction = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'readAction'))
    testable = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'testable'))
    
  
    abList = list()
    if ipxactConfig.output == outputType.c:
        if name is not None:
            abList.append(["NAME", "\"" + name + "\""])
        if usage is not None:
            abList.append(["USAGE", "\"" + usage + "\""])
        if baseAddress is not None:
            abList.append(["BASEADDRESS", baseAddress])
        if range is not None:
            abList.append(["RANGE", _range])
        if width is not None:
            abList.append(["WIDTH", width])
        if description is not None:
            abList.append(["DESCRIPTION", "\"" + description + "\""])
        if access is not None:
            abList.append(["ACCESS", convAccessTypeToDefine(access)])
        if volatile is not None:
            abList.append(["VOLATILE", convBool(volatile)])
        if modifiedWriteValue is not None:
            abList.append(["MODIFIEDWRITEVALUE", convModifedWriteValueTypeToDefine(modifiedWriteValue) ])
        if readAction is not None:
            abList.append(["READACTION", convReadActionTypeToDefine(readAction) ])
        if testable is not None:
            abList.append(["TESTABLE", convBool(testable) ])
            
    elif ipxactConfig.output == outputType.vhdl: 
        if name is not None:
            abList.append(["NAME", ": string", "\"" + name + "\""])
        if usage is not None:
            abList.append(["USAGE", ": string", "\"" + usage + "\""])
        if baseAddress is not None:
            abList.append(["BASEADDRESS", ": std_logic_vector(" + str(ipxactConfig.abBaseAddressWidth-1) + " downto 0)", intToVhdlNumStr(getScaledNonNegativeInteger(baseAddress), ipxactConfig.abBaseAddressWidth, ipxactConfig.abBaseAddressFormat)])
        if range is not None:
            abList.append(["RANGE", ": integer", _range])
        if width is not None:
            abList.append(["WIDTH", ": integer", width])
        if description is not None:
            abList.append(["DESCRIPTION", ": string", "\"" + description + "\""])
        if access is not None:
            abList.append(["ACCESS", ": spiritAccessType", convAccessTypeToDefine(access)])
        if volatile is not None:
            abList.append(["VOLATILE", ": boolean", convBool(volatile)])
        if modifiedWriteValue is not None:
            abList.append(["MODIFIEDWRITEVALUE", ": spiritModifiedWriteValueType", convModifedWriteValueTypeToDefine(modifiedWriteValue) ])
        if readAction is not None:
            abList.append(["READACTION", ": spiritReadActionType", convReadActionTypeToDefine(readAction) ])
        if testable is not None:
            abList.append(["TESTABLE", ": boolean", convBool(testable) ])       
        
    return abList;
  
  

def abPrint(root, ipxactConfig):
    addressBlockElementList = getAddressBlockElementList(root)
    
    printStr = ""

    for addressBlockElement in addressBlockElementList:
        abStringsList = getAddressBlockStringsAsList(addressBlockElement, ipxactConfig)
        abColumnMaxLengths = getMaxLengtOfColumnsAsList(abStringsList)
        compName = ifNotNoneReturnText(root.find('./' + IPXACT_NS + 'name'))
        abName = ifNotNoneReturnText(addressBlockElement.find(IPXACT_NS + 'name'))
        
        if ipxactConfig.output == outputType.vhdl:
            #constant INTR_BLOCK_BASEADDR : std_logic_vector(63 downto 0) := X"0000000000000000";
            printStr += "\n\n-- Addressblock " + abName + " --"
            formatStr = "constant {0}_{1}_{{{2}}} {{{3}}} := {{{4}}};".format(compName.upper(), abName.upper(), "0:<" + str(abColumnMaxLengths[0]), "1:<" + str(abColumnMaxLengths[1]), "2:<")
        elif ipxactConfig.output == outputType.c:
            printStr += "\n\n/* Addressblock " + abName + " */"
            formatStr = "#define {0}_{1}_{{{2}}}\t{{{3}}}".format(compName.upper(), abName.upper(), "0:<" + str(abColumnMaxLengths[0]), "1:<" + str(abColumnMaxLengths[1]))
        
        
        for abStrings in abStringsList:
            if ipxactConfig.output == outputType.vhdl:
                printStr += "\n" + formatStr.format(abStrings[0], abStrings[1], abStrings[2])
            elif ipxactConfig.output == outputType.c:
                printStr += "\n" + formatStr.format(abStrings[0], abStrings[1])
            
    return printStr

def regPrint(root, ipxactConfig):
    registerElementList = getRegisterElementList(root)
    
    printStr = ""
    
    for registerElement in registerElementList:
        regStringsList = getRegisterStringsAsList(registerElement, ipxactConfig)
        regColumnMaxLengths = getMaxLengtOfColumnsAsList(regStringsList)
        compName = ifNotNoneReturnText(root.find('./' + IPXACT_NS + 'name'))
        abName = ifNotNoneReturnText(registerElement.find("../%sname" % IPXACT_NS))
        regName = ifNotNoneReturnText(registerElement.find(IPXACT_NS + 'name'))
        if ipxactConfig.output == outputType.vhdl:
            printStr +=  "\n\n-- Register " + regName + " --"
            formatStr = "constant {0}_{1}_{2}_{{{3}}} {{{4}}} := {{{5}}};".format(compName.upper(), abName.upper(), regName.upper(), "0:<" + str(regColumnMaxLengths[0]), "1:<" + str(regColumnMaxLengths[1]), "2:<")
        elif ipxactConfig.output == outputType.c:
            printStr +=  "\n\n/* Register " + regName + " */"
            formatStr = "#define {0}_{1}_{2}_{{{3}}}\t{{{4}}}".format(compName.upper(), abName.upper(), regName.upper(), "0:<" + str(regColumnMaxLengths[0]), "1:<" + str(regColumnMaxLengths[1]))
                  
        for regStrings in regStringsList:
            if ipxactConfig.output == outputType.vhdl:
                printStr += "\n" + formatStr.format(regStrings[0], regStrings[1], regStrings[2])
            elif ipxactConfig.output == outputType.c:
                printStr += "\n" + formatStr.format(regStrings[0], regStrings[1])
            
    return printStr

def fieldsPrint(root, ipxactConfig):
    fieldElementList = getFieldElementList(root)
    
    printStr = ""
    
    for fieldElement in fieldElementList:
        fieldStringsList = getFieldStringsAsList(fieldElement, ipxactConfig)
        fieldColumnMaxLengths = getMaxLengtOfColumnsAsList(fieldStringsList)
        compName = ifNotNoneReturnText(root.find('./' + IPXACT_NS + 'name'))
        abName = ifNotNoneReturnText(fieldElement.find("../../%sname" % IPXACT_NS))
        regName = ifNotNoneReturnText(fieldElement.find("../%sname" % IPXACT_NS))
        fieldName = ifNotNoneReturnText(fieldElement.find(IPXACT_NS + 'name'))
        if ipxactConfig.output == outputType.vhdl:
            printStr +=  "\n\n-- Field " + fieldName + " --"
            formatStr = "constant {0}_{1}_{2}_{3}_{{{4}}} {{{5}}} := {{{6}}};".format(compName.upper(), abName.upper(), regName.upper(), fieldName.upper(), "0:<" + str(fieldColumnMaxLengths[0]), "1:<" + str(fieldColumnMaxLengths[1]), "2:<")
        elif ipxactConfig.output == outputType.c:
            printStr +=  "\n\n/* Field " + fieldName + " */"
            formatStr = "#define {0}_{1}_{2}_{3}_{{{4}}}\t{{{5}}}".format(compName.upper(), abName.upper(), regName.upper(), fieldName.upper(), "0:<" + str(fieldColumnMaxLengths[0]), "1:<" + str(fieldColumnMaxLengths[1]))
    
        for fieldStrings in fieldStringsList:
            if ipxactConfig.output == outputType.vhdl:
                printStr += "\n" + formatStr.format(fieldStrings[0], fieldStrings[1], fieldStrings[2])
            elif ipxactConfig.output == outputType.c:
                printStr += "\n" + formatStr.format(fieldStrings[0], fieldStrings[1])
            
    return printStr
                    
            
class outputType:
    vhdl = 0
    c = 1
    cpp = 2
    

class outputConfig():
    output = outputType.vhdl
    abBaseAddressWidth = 64
    abBaseAddressFormat = formatEnum.hex
    regAddressOffsetWidth = 32
    regAddressOffsetFormat = formatEnum.hex
    regResetMaskWidth = 32
    regResetMaskFormat = formatEnum.hex
    regResetValueWidth = 32
    regResetValueFormat = formatEnum.hex
    regBaseAddressOffsetWidth = 32
    regBaseAddressOffsetFormat = formatEnum.hex
    



def vhdlFilePrint(root, ipxactConfig):
    printStr = ''
    printStr += VHDL_HEADER
    printStr += VHDL_SPIRIT_TYPES
    printStr += abPrint(root, ipxactConfig)
    printStr += regPrint(root,  ipxactConfig)
    printStr += fieldsPrint(root,  ipxactConfig)
    printStr += VHDL_FOOTER
        
    return printStr
    
            
            
def cFilePrint(root, ipxactConfig):
    printStr = ''
    printStr += C_PRAGMA_ONCE
    printStr += C_SPIRIT_TYPES
    printStr += abPrint(root, ipxactConfig)
    printStr += regPrint(root, ipxactConfig)
    printStr += fieldsPrint(root, ipxactConfig)
    
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
        parser.add_argument('-abBaseAddressWidth', help="width of std_logic_vector in generated addressblock address output [default: %(default)s]", metavar='width', default=64, type=int)
        parser.add_argument('-abBaseAddressFormat', help="format of std_logic_vector in generated addressblock address output [default: %(default)s]", metavar='format', default="hex")
        parser.add_argument('-regAddressOffsetWidth', help="width of std_logic_vector in generated register address offset output [default: %(default)s]", metavar='width', default=32, type=int)
        parser.add_argument('-regAddressOffsetFormat', help="format of std_logic_vector in generated register address offset output [default: %(default)s]", metavar='format', default="hex")
        parser.add_argument('-regResetMaskWidth', help="width of std_logic_vector in generated register reset mask output [default: %(default)s]", metavar='width', default=64, type=int)
        parser.add_argument('-regResetMaskFormat', help="format of std_logic_vector in generated register reset mask output [default: %(default)s]", metavar='format', default="hex")
        parser.add_argument('-regResetValueWidth', help="width of std_logic_vector in generated register reset value output [default: %(default)s]", metavar='width', default=32, type=int)
        parser.add_argument('-regResetValueFormat', help="format of std_logic_vector in generated register reset value output [default: %(default)s]", metavar='format', default="hex")
        parser.add_argument('-regBaseAddressOffsetWidth', help="width of std_logic_vector in generated register address offset output [default: %(default)s]", metavar='width', default=32, type=int)
        parser.add_argument('-regBaseAddressOffsetFormat', help="format of std_logic_vector in generated register address offset mask output [default: %(default)s]", metavar='format', default="hex")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument(dest="outdir", help="path to output directory [default: %(default)s]", nargs='?' , default= os.path.join(os.path.dirname(os.path.dirname(__file__)),"out"))
        
        # Process arguments
        args = parser.parse_args()
  
        if args.verbose:
            log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG, stream=sys.stdout)
        else:
            log.basicConfig(format="%(levelname)s: %(message)s")
                  
        if args.inpath is not None:
            inpath = os.path.normpath(args.inpath)
        
        if args.outdir is not None:
            outdir = os.path.abspath(os.path.normpath(args.outdir))
    
        log.info("Input path: %s" % inpath)
        log.info("Out directory: %s" % outdir)
            
        if args.vhdl:
            ipxactConfigVHDL = outputConfig()
            ipxactConfigVHDL.output = outputType.vhdl
            ipxactConfigVHDL.abBaseAddressWidth = args.abBaseAddressWidth
            ipxactConfigVHDL.abBaseAddressFormat = args.abBaseAddressFormat
            ipxactConfigVHDL.regAddressOffsetWidth = args.regAddressOffsetWidth
            ipxactConfigVHDL.regAddressOffsetFormat = args.regAddressOffsetFormat
            ipxactConfigVHDL.regResetMaskWidth = args.regResetMaskWidth
            ipxactConfigVHDL.regResetMaskFormat = args.regResetMaskFormat
            ipxactConfigVHDL.regResetValueWidth = args.regResetValueWidth
            ipxactConfigVHDL.regResetValueFormat = args.regResetValueFormat
            ipxactConfigVHDL.regBaseAddressOffsetWidth = args.regBaseAddressOffsetWidth
            ipxactConfigVHDL.regBaseAddressOffsetFormat = args.regBaseAddressOffsetFormat
            
        if args.c:
            ipxactConfigC = outputConfig()
            ipxactConfigC.output = outputType.c
            
        try:
            root = openXMLFileReturnRoot(inpath)
            
            if args.vhdl:
                printStr = vhdlFilePrint(root, ipxactConfigVHDL)
                if not os.path.exists(outdir):
                    os.makedirs(outdir)
                fileStr = os.path.join(outdir,getComponentName(root).lower() + "_regs.vhd")
                with open(fileStr, "w") as f:
                    f.write(printStr)
                    log.info("Wrote vhdl package to %s" % fileStr)
        
        
            if args.c:
                printStr = cFilePrint(root, ipxactConfigC)
                if not os.path.exists(outdir):
                    os.makedirs(outdir)
                fileStr = os.path.join(outdir,getComponentName(root).lower() + "_regs.h")
                with open(fileStr, "w") as f:
                    f.write(printStr)
                    log.info("Wrote c header to %s" % fileStr)
                
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
        #sys.argv.append("-h")
        sys.argv.append("-v")
        #sys.argv.append("-V")
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
    

