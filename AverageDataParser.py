
import numpy
import ConfigParser
from math import sqrt


def stripLeadingDigits( word ):
    for i in range( len( word ) ):
        if word[i].isalpha():
            return word[i:]


class AverageDataParser:

    # C-tor, read inputs and calculate covariances:
    def __init__( self, filename ):
        self.__correlations= None
        self.__filename= filename
        self.__readInput( filename )
        return

    # Read inputs using ConfigParser:
    def __readInput( self, filename ):
        parser= ConfigParser.ConfigParser()
        parser.read( filename )
        self.__readData( parser )
        self.__readCovariances( parser )
        self.__makeCovariances()
        return

    # Read "Data" section:
    def __readData( self, parser ):
        tuplelist= parser.items( "Data" )
        herrors= {}
        hcovopt= {}
        for item in tuplelist:
            key= item[0]
            value= item[1]
            if key == "names":
                names= value
            elif key == "values":
                ldata= [ float(s) for s in value.split() ]
            else:
                listvalue= value.split()
                hcovopt[key]= listvalue.pop()
                herrors[key]= [ float(s) for s in listvalue ]
        for key in herrors.keys():
            if "%" in hcovopt[key]:
                for ierr in range( len(herrors[key]) ):
                    herrors[key][ierr]*= ldata[ierr]/100.0
        self.__names= names.split()
        self.__inputs= ldata
        self.__covopts= hcovopt
        self.__errors= herrors
        return

    # Read "Covariances" section if it exists:
    def __readCovariances( self, parser ):
        hcovopt= self.__covopts
        if sum( [ "c" in v or "m" in v for v in hcovopt.values() ] ):
            hcovlists= {}
            for key in hcovopt.keys():
                if "c" in hcovopt[key] or "m" in hcovopt[key]:
                    covvalues= parser.get( "Covariances", key ).split()
                    if "c" in hcovopt[key]:
                        hcovlists[key]= [ float(s) for s in covvalues ]
                    elif "m" in hcovopt[key]:
                        hcovlists[key]= covvalues
            self.__correlations= hcovlists
        return

    # Calculate covariances from inputs and keep as numpy matrices:
    def __makeZeroMatrix( self ):
        ndim= len( self.__inputs )
        return numpy.matrix( numpy.zeros( shape=(ndim,ndim) ) )
    def __makeMatrixFromList( self, lelements ):
        m= numpy.matrix( lelements )
        ndim= len( self.__inputs )
        m.shape= ( ndim, ndim )
        return m
    def __calcCovariance( self, covoption, err1, err2, iderr1, iderr2 ):
        if "f" in covoption:
            cov= err1*err2
        elif "a" in covoption:
            cov= -err1*err2
        elif "p" in covoption:
            cov= min( err1, err2 )**2
        elif "u" in covoption:
            if iderr1 == iderr2:
                cov= err1**2
            else:
                cov= 0.0
        return cov
    def __makeCovariances( self ):
        hcov= {}
        cov= self.__makeZeroMatrix()
        for errorkey in self.__errors.keys():
            lcov= []
            errors= self.__errors[errorkey] 
            covoption= self.__covopts[errorkey]
            iderr1= 0
            if "g" in covoption:
                minerr= min( errors )
            for err1 in errors:
                iderr1+= 1
                iderr2= 0
                for err2 in errors:
                    iderr2+= 1
                    # Global options, all covariances according to
                    # same rule gp, p, f or u:
                    if "gp" in covoption:
                        if iderr1 == iderr2:
                            covelement= err1**2
                        else:
                            covelement= minerr**2
                    # Direct calculation from "f", "p" or "u":
                    elif( "f" in covoption or "p" in covoption or
                          "u" in covoption or "a" in covoption ):
                        covelement= self.__calcCovariance( covoption,
                                                           err1, err2, 
                                                           iderr1, iderr2 )
                    # Covariances from correlations and errors:
                    elif "c" in covoption:
                        idx= len( lcov )
                        corrlist= self.__correlations[errorkey]
                        covelement= corrlist[idx]*err1*err2
                    # Covariances from options:
                    elif "m" in covoption:
                        idx= len( lcov )
                        mcovopts= self.__correlations[errorkey]
                        mcovopt= mcovopts[idx]
                        covelement= self.__calcCovariance( mcovopt,
                                                           err1, err2, 
                                                           iderr1, iderr2 )
                    else:
                        print "Option", covoption, "not recognised"
                        return
                    lcov.append( covelement )
            m= self.__makeMatrixFromList( lcov )
            cov+= m
            hcov[errorkey]= m
        self.__hcov= hcov
        self.__cov= cov
        return

    # Print inputs:
    def printInputs( self, keys=None ):
        if keys == None:
            keys= self.__errors.keys()
            keys.sort()
        print "\n AverageDataParser: input from", self.__filename
        print "\n Variables:", 
        for name in self.__names:
            print "{0:>10s}".format( name ),
        print "Covariance option"
        print "\n    Values:", 
        for value in self.__inputs:
            print "{0:10.4f}".format( value ),
        print
        for key in keys:
            print "{0:>10s}:".format( stripLeadingDigits( key ) ),
            for error in self.__errors[key]:
                print "{0:10.4f}".format( error ),
            print self.__covopts[key]
        totalerrors= self.getTotalErrors()
        print "\n     total:",
        for error in totalerrors:
            print "{0:10.4f}".format( error ),
        print
        if self.__correlations:
            print "\nCorrelations:"
            keys= self.__correlations.keys()
            keys.sort()
            for key in keys:
                print "\n{0:s}:".format( stripLeadingDigits( key ) )
                covopt= self.__covopts[key]
                correlations= self.__correlations[key]
                n= int( sqrt( len(correlations) ) )
                for i in range(n):
                    for j in range(n):
                        ii= i*n+j
                        if "c" in covopt:
                            print "{0:4.2f}".format( correlations[ii] ),
                        else:
                            print correlations[ii],
                    print
        return

    # Retrieve values:
    def getFilename( self ):
        return str( self.__filename )
    def getNames( self ):
        return list( self.__names )
    def getValues( self ):
        return list( self.__inputs )
    def getErrors( self ):
        return dict( self.__errors )
    def getTotalErrors( self ):
        totalerrors= len( self.__inputs )*[0]
        for errors in self.__errors.values():
            for ierr in range( len( errors ) ):
                totalerrors[ierr]+= errors[ierr]**2
        for ierr in range( len( totalerrors ) ):
            totalerrors[ierr]= sqrt( totalerrors[ierr] )      
        return totalerrors
    def getCovoption( self ):
        return dict( self.__covopts )
    def getCorrelations( self ):
        if self.__correlations == None:
            return None
        else:
            return dict( self.__correlations )
    def getCovariances( self ):
        return dict( self.__hcov )
    def getTotalCovariance( self ):
        return self.__cov.copy()

