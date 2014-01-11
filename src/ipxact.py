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
import xml.etree.ElementTree as ET

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2014-01-02'
__updated__ = '2014-01-02'

DEBUG = 0
TESTRUN = 1
PROFILE = 0

IPXACT_NS = '{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5}'

C_HEADER_DIV = "/*****************************************************************************/"

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg
    
def ifNotNoneReturnText(element):
    if element is not None:
        return element.text
    else:
        return "?"
 
def openXMLFileReturnRoot(path):   
    if os.path.exists(os.path.abspath(path)):
        log.info("Opening file: %s", path)
        tree = ET.parse(path)
        root = tree.getroot() 
        return root
    else:
        raise IOError(2, "File does not exist, file:%s" %os.path.abspath(path))
    
    
class AddressBlock():
    def __init__(self, name, baseAddress, _range, width, usage, description):
        self.name = name
        self.baseAddress = baseAddress
        self.range = _range
        self.width = width
        self.usage = usage
        self.description = description

def isHex(string):
    if string[0:2] == "0x" or string[0] == '#':
        return True
    else:
        return False
    
def getIPXACTNumber(element):
    if isHex(element):
        return int(element, 16)
    else:
        return int(element)
    
def positiveIntegerGet():
    pass

def scaledIntegerGet():
    pass

def scaledNonNegativeIntegerGet():
    pass

def scaledPositiveIntegerGet():
    pass

def SpiritURIGet():
    pass


    
def getAddressBlocksFromMemoryMapElement(memoryMapElement):
                addrressBlockElementList = memoryMapElement.findall(IPXACT_NS + 'addressBlock')
                
                addressBlockList = list()
                for addrressBlockElement in addrressBlockElementList:
                    addressBlockList.append(AddressBlock(addrressBlockElement.find(IPXACT_NS + 'name').text, addrressBlockElement.find(IPXACT_NS + 'baseAddress').text))
                    name = addrressBlockElement.find(IPXACT_NS + 'name').text
                    baseAddress = getIPXACTNumber(addrressBlockElement.find(IPXACT_NS + 'baseAddress').text)
                    #addressBlockRange       = addrressBlockElement.find(IPXACT_NS + 'range'         )
                    #addressBlockWidth       = addrressBlockElement.find(IPXACT_NS + 'width'         )
                    #addressBlockUsage       = addrressBlockElement.find(IPXACT_NS + 'usage'         )
                    #addressBlockDesc        = addrressBlockElement.find(IPXACT_NS + 'description'   )  
                    
                    strReturn[i]= "#define " + addressBlockName.text.upper() + "_BASE_ADDR " + addressBlockBaseAddress.text + " /* Base address offset */\n" 
                    lenName.append(len(addressBlockName.text()))
           
    
def printAddressBlockList(addressBlockList):
    for addressBlock.name in addressBlockList
    
    
def ipxactParseAsText(path):
        root = openXMLFileReturnRoot(path)
        
        componentName = root.find(IPXACT_NS + 'name')
        
        memoryMapsElementList = root.findall(IPXACT_NS +'memoryMaps')
        
        strIndent = ""
        
        strReadOut = (C_HEADER_DIV + "\n" +
                      "#ifndef " + componentName.text.upper() + "_H" + "\n" +
                      "#define " + componentName.text.upper() + "_H"+  "\n" +
                      C_HEADER_DIV + "\n"
                      )
        
        for memoryMapsElement in memoryMapsElementList:
            memoryMapElementList = memoryMapsElement.findall(IPXACT_NS + 'memoryMap')
            for memoryMapElement in memoryMapElementList:
                memoryMapName = memoryMapElement.find(IPXACT_NS + 'name'        )
                memoryMapDesc = memoryMapElement.find(IPXACT_NS + 'description' )
                log.info(strIndent + "Memory Map:")
                strIndent += "\t"
                log.info(strIndent + "Name:        %s" %ifNotNoneReturnText(memoryMapName))
                log.info(strIndent + "Description: %s" %ifNotNoneReturnText(memoryMapDesc))
                

                
                addrressBlockElementList = memoryMapElement.findall(IPXACT_NS + 'addressBlock')
                for addrressBlockElement in addrressBlockElementList:
                    addressBlockName        = addrressBlockElement.find(IPXACT_NS + 'name'          )
                    addressBlockBaseAddress = addrressBlockElement.find(IPXACT_NS + 'baseAddress'   )
                    addressBlockRange       = addrressBlockElement.find(IPXACT_NS + 'range'         )
                    addressBlockWidth       = addrressBlockElement.find(IPXACT_NS + 'width'         )
                    addressBlockUsage       = addrressBlockElement.find(IPXACT_NS + 'usage'         )
                    addressBlockDesc        = addrressBlockElement.find(IPXACT_NS + 'description'   )                    
                    
                    log.info(strIndent + "Address block:")
                    strIndent = strIndent + "\t"
                    log.info(strIndent + "Name:         %s" %ifNotNoneReturnText(addressBlockName))
                    log.info(strIndent + "Base address: %s" %ifNotNoneReturnText(addressBlockBaseAddress))
                    log.info(strIndent + "Range:        %s" %ifNotNoneReturnText(addressBlockRange))
                    log.info(strIndent + "Width:        %s" %ifNotNoneReturnText(addressBlockWidth))
                    log.info(strIndent + "Usage         %s" %ifNotNoneReturnText(addressBlockUsage))
                    log.info(strIndent + "Description:  %s" %ifNotNoneReturnText(addressBlockDesc))
                    
                    strReadOut +=  ("\n" +  "\n/* Address Block: */\n" +
                      "#define " + addressBlockName.text.upper() + "_BASE_ADDR " + addressBlockBaseAddress.text + " /* Base address offset */\n" 
                      )
                    
                    strReadOut += "\n /* Registers */\n"
                    registerElementList = addrressBlockElement.findall(IPXACT_NS + 'register')
                    for registerElement in registerElementList:
                        registerElementName            = registerElement.find(IPXACT_NS + 'name'         )
                        registerElementDescription     = registerElement.find(IPXACT_NS + 'description'  )
                        registerElementDim             = registerElement.find(IPXACT_NS + 'dim'          )
                        registerElementAddressOffset   = registerElement.find(IPXACT_NS + 'addressOffset')
                        registerElementSize            = registerElement.find(IPXACT_NS + 'size'         )
                        registerElementVolatile        = registerElement.find(IPXACT_NS + 'volatile'     )
                        registerElementAccess          = registerElement.find(IPXACT_NS + 'access'       )
                        registerElementReset           = registerElement.find(IPXACT_NS + 'reset'        )
                        
                        log.info(strIndent + "Register:")
                        strIndent = strIndent + "\t"
                        log.info(strIndent + "Name         : %s" %ifNotNoneReturnText(registerElementName))
                        log.info(strIndent + "Description  : %s" %ifNotNoneReturnText(registerElementDescription))
                        log.info(strIndent + "Dim          : %s" %ifNotNoneReturnText(registerElementDim))
                        log.info(strIndent + "AddressOffset: %s" %ifNotNoneReturnText(registerElementAddressOffset))
                        log.info(strIndent + "Size         : %s" %ifNotNoneReturnText(registerElementSize))
                        log.info(strIndent + "Volatile     : %s" %ifNotNoneReturnText(registerElementVolatile))
                        log.info(strIndent + "Access       : %s" %ifNotNoneReturnText(registerElementAccess))
                        log.info(strIndent + "Reset        : %s" %ifNotNoneReturnText(registerElementReset))
                        
                        strReadOut +=  (
                                        "#define " + registerElementName.text.upper() + "_ADDR_OFFSET " + registerElementAddressOffset.text + " /* Address block offset */\n" 
                                        )
                                            
                        fieldElementList = registerElement.findall(IPXACT_NS + 'field')
                        for fieldElement in fieldElementList:
                            fieldElementName                = fieldElement.find(IPXACT_NS + 'name')
                            fieldElementDescription         = fieldElement.find(IPXACT_NS + 'description')
                            fieldElementBitOffset           = fieldElement.find(IPXACT_NS + 'bitOffset')
                            fieldElementBitWidth            = fieldElement.find(IPXACT_NS + 'bitWidth')
                            fieldElementVolatile            = fieldElement.find(IPXACT_NS + 'volatile')
                            fieldElementAccess              = fieldElement.find(IPXACT_NS + 'access')
                            fieldElementModifiedWriteValue  = fieldElement.find(IPXACT_NS + 'modifiedWriteValue')
                            fieldElementTestable            = fieldElement.find(IPXACT_NS + 'testable')
                                
                            log.info(strIndent + "Field:")
                            strIndent += "\t"                                
                            log.info(strIndent + "Name                : %s" %ifNotNoneReturnText(fieldElementName                   ))
                            log.info(strIndent + "Description         : %s" %ifNotNoneReturnText(fieldElementDescription            ))
                            log.info(strIndent + "BitOffset           : %s" %ifNotNoneReturnText(fieldElementBitOffset              ))
                            log.info(strIndent + "BitWidth            : %s" %ifNotNoneReturnText(fieldElementBitWidth               ))
                            log.info(strIndent + "Volatile            : %s" %ifNotNoneReturnText(fieldElementVolatile               ))
                            log.info(strIndent + "Access              : %s" %ifNotNoneReturnText(fieldElementAccess                 ))
                            log.info(strIndent + "ModifiedWriteValue  : %s" %ifNotNoneReturnText(fieldElementModifiedWriteValue     ))
                            log.info(strIndent + "Testable            : %s" %ifNotNoneReturnText(fieldElementTestable               ))




                        
                            strIndent = strIndent[:-1]
                        strIndent = strIndent[:-1]
                    strIndent = strIndent[:-1]
                strIndent = strIndent[:-1]
                
                strOutCFilePath = os.path.join(os.getcwd(), "out", componentName.text.lower() + ".h")
                try:
                    fOutCFile = open(strOutCFilePath, 'w')
                    fOutCFile.write(strReadOut)
                except IOError:
                    raise
                else:
                    log.info("File: %s written successfully" %strOutCFilePath)
        
        
        


def main(argv=None): # IGNORE:C0111
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
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument(dest="paths", help="paths to folder(s) with source file(s) [default: %(default)s]", metavar="path", nargs='+')
        
        # Process arguments
        args = parser.parse_args()
        
        paths = args.paths
        
        if args.verbose:
            log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG, stream=sys.stdout)
        else:
            log.basicConfig(format="%(levelname)s: %(message)s")
    
        log.info("Paths: %s" %paths)
            
        for path in paths:
            try:
                ipxactParseAsText(path)
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