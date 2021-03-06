
import numpy
import ConfigParser
from math import sqrt, log


def stripLeadingDigits( word ):
    for i in range( len( word ) ):
        if word[i].isalpha():
            return word[i:]


class AverageDataParser:

    # C-tor, read inputs and calculate covariances:
    def __init__( self, filename, llogNormal=False ):
        self.__correlations= None
        self.__filename= filename
        self.__readInput( filename, llogNormal )
        return

    # Read inputs using ConfigParser:
    def __readInput( self, filename, llogNormal ):
        parser= ConfigParser.ConfigParser()
        parser.read( filename )
        self.__readData( parser )
        self.__readGlobals( parser )
        self.__readCovariances( parser )
        if llogNormal:
            self.__transformLogNormal()
        self.__makeCovariances()
        return

    def __transformLogNormal( self ):
        herrors= {}
        for key in self.__errors.keys():
            errors= [ error/value for ( error, value ) in zip( self.__errors[key], self.__inputs  ) ]
            herrors[key]= errors
        self.__errors= herrors
        self.__inputs= [ log( value ) for value in self.__inputs ]
        return

    # Read "Data" section:
    def __readData( self, parser ):
        tuplelist= parser.items( "Data" )
        herrors= {}
        hcovopt= {}
        grouplist= None
        for item in tuplelist:
            key= item[0]
            value= item[1]
            listvalue= value.split()
            if key == "names":
                names= listvalue
            elif key == "values":
                ldata= [ float(s) for s in listvalue ]
            elif key == "groups":
                grouplist= listvalue
            else:
                hcovopt[key]= listvalue.pop()
                herrors[key]= [ float(s) for s in listvalue ]
        for key in herrors.keys():
            if "%" in hcovopt[key]:
                for ierr in range( len(herrors[key]) ):
                    herrors[key][ierr]*= ldata[ierr]/100.0
        if grouplist is None:
            grouplist= [ "a" for name in names ]
        self.__names= names
        self.__inputs= ldata
        self.__covopts= hcovopt
        self.__errors= herrors
        self.__groups= grouplist
        groupset= set( grouplist )
        ngroups= len( groupset )
        groups= sorted( groupset )
        groupmatrix= []
        for g in grouplist:
            groupmatrixrow= ngroups*[0]
            index= groups.index( g )
            groupmatrixrow[index]= 1
            groupmatrix.append( groupmatrixrow )
        self.__groupmatrix= groupmatrix
        return

    def __readGlobals( self, parser ):
        hglobals= {}
        try:
            tuplelist= parser.items( "Globals" )
        except ConfigParser.NoSectionError:
            pass
        else:
            for item in tuplelist:
                key= item[0]
                value= item[1]
                if key == "correlationfactor":
                    hglobals[key]= float( value )
        self.__hglobals= hglobals
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
    def __calcCovariance( self, covoption, errors, iderr1, iderr2 ):
        err1= errors[iderr1]
        err2= errors[iderr2]
        if "f" in covoption:
            cov= err1*err2
        elif "a" in covoption:
            if iderr1 == iderr2:
                cov= err1**2
            else:
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
        # The covariance matrices for each error source
        hcov= {}
        # The covariance matrices without fully correlated error components
        # for each error source
        hredcov= {}
        systerrormatrix= {}
        errorkeys= sorted( self.__errors.keys() )
        for errorkey in errorkeys:
            nerr= errorkeys.index( errorkey )
            lcov= []
            lredcov= []
            errors= self.__errors[errorkey] 
            nerrors= len( errors )
            covoption= self.__covopts[errorkey]
            # Global options, all covariances according to
            # same rule gp, p, f or u:
            if "gpr" in covoption:
                minrelerr= min( [ err/value for err, value in 
                                  zip( errors, self.__inputs ) if err > 0.0 ] )
                systerrlist= []
                for iderr1 in range( nerrors ):
                    for iderr2 in range( nerrors ):
                        if iderr1 == iderr2:
                            covelement= errors[iderr1]**2
                            redcovelement= errors[iderr1]**2 - (minrelerr*self.__inputs[iderr1])**2
                            redcovelement= max( redcovelement, 0.0 )
                        else:
                            covelement= minrelerr**2*self.__inputs[iderr1]*self.__inputs[iderr2]                            
                            redcovelement= 0.0
                        lcov.append( covelement )
                        lredcov.append( redcovelement )
                    systerrlist.append( minrelerr*self.__inputs[iderr1] )
                systerrormatrix[nerr]= systerrlist
            elif( "gp" in covoption ):
                minerr= min( [ error for error in errors if error > 0.0 ] )
                systerrlist= []
                for iderr1 in range( nerrors ):
                    for iderr2 in range( nerrors ):
                        if iderr1 == iderr2:
                            covelement= errors[iderr1]**2
                            redcovelement= errors[iderr1]**2 - minerr**2
                        else:
                            covelement= minerr**2
                            redcovelement= 0.0
                        lcov.append( covelement )
                        lredcov.append( redcovelement )
                    systerrlist.append( minerr )
                systerrormatrix[nerr]= systerrlist
            # Direct calculation from "f", "p", "u" or "a":
            elif( "f" in covoption or "p" in covoption or
                  "u" in covoption or "a" in covoption ):
                lcov= [ self.__calcCovariance( covoption, errors, iderr1, iderr2 )
                        for iderr1 in range( nerrors ) 
                        for iderr2 in range( nerrors ) ]
                if( "f" in covoption ):
                    systerrormatrix[nerr]= errors
                    lredcov= len(errors)**2*[0.0]
                else:
                    lredcov= lcov
            # Covariances from correlations and errors:
            elif "c" in covoption:
                corrlist= self.__correlations[errorkey]
                err1err2= [ err1*err2 for err1 in errors for err2 in errors ]
                lcov= [ corr*errprod 
                        for corr, errprod in zip( corrlist, err1err2 ) ]
                # "Onionisation":
                if "o" in covoption:
                    for iderr1 in range( nerrors ):
                        for iderr2 in range( nerrors ):
                            if errors[iderr1] > 0.0 and errors[iderr2] > 0.0:
                                ierr= iderr1*nerrors+iderr2
                                lcov[ierr]= min( lcov[ierr],
                                                 min( errors[iderr1], errors[iderr2] )**2 )
                lredcov= lcov
            # Covariances from options:
            elif "m" in covoption:
                mcovopts= self.__correlations[errorkey]
                iderr1err2= [ ( iderr1, iderr2 ) for iderr1 in range( nerrors )
                                for iderr2 in range( nerrors ) ]
                lcov= [ self.__calcCovariance( mcovopt, errors, iderr[0], iderr[1] )
                        for mcovopt, iderr in zip( mcovopts, iderr1err2 ) ]
                if( "f" in mcovopts and not "p" in mcovopts ):
                    systerrormatrix[nerr]= errors
                    lredcov= len(errors)**2*[0.0]
                else:
                    lredcov= lcov

            # Error in option:
            else:
                print "Option", covoption, "not recognised"
                return

            m= self.__makeMatrixFromList( lcov )

            if self.__hglobals.has_key( "correlationfactor" ):
                for i in range( m.shape[0] ):
                    for j in range( m.shape[1] ):
                        if i != j and m[i,i]*m[j,j] != 0.0:
                            m[i,j]*= m[i,j]/(sqrt(m[i,i]*m[j,j]))*self.__hglobals["correlationfactor"]


            redm= self.__makeMatrixFromList( lredcov )
            hcov[errorkey]= m
            hredcov[errorkey]= redm

        # Build final full and reduced covariance matrices, reduced means
        # all errors except fully correlated (see above)
        cov= self.__makeZeroMatrix()
        redcov= self.__makeZeroMatrix()
        for errorkey in errorkeys:
            redcov+= hredcov[errorkey]
        for errorkey in errorkeys:
            # Covariance matrix a la Neudecker et al and Bohm und Zech
            covoption= self.__covopts[errorkey]
            if "q" in covoption:
                # Average with "not fully" correlated errors for
                # calculation of fully correlated cov.matrix elements
                gm= numpy.matrix( self.__groupmatrix )
                inv= redcov.getI()
                utvinvu= gm.getT()*inv*gm
                utvinvuinv= utvinvu.getI()
                wm= utvinvuinv*gm.getT()*inv
                values= numpy.matrix( self.__inputs )
                values.shape= ( len( self.__inputs ), 1 )
                avg= wm*values
                # fully correlated cov.matrix elements
                errors= numpy.matrix( self.__errors[errorkey] )
                errors.shape= ( len( self.__inputs ), 1 )
                relerrs= errors/values
                avgrelerrs= numpy.multiply( gm*avg, relerrs )
                lcov= avgrelerrs*avgrelerrs.T
            else:
                lcov= hcov[errorkey]
            cov+= lcov
            
        # Keep results as members:
        self.__hcov= hcov
        self.__hredcov= hredcov
        self.__cov= cov
        self.__redcov= redcov
        self.__systerrormatrix= systerrormatrix

        return

    # Print inputs:
    def printInputs( self, keys=None ):
        if keys is None:
            keys= self.__errors.keys()
            keys.sort()
        print "\n AverageDataParser: input from", self.__filename
        print "\n Variables:", 
        for name in self.__names:
            print "{0:>10s}".format( name ),
        print "Covariance option"
        if len( set( self.__groups ) ) > 1:
            print "\n    Groups:", 
            for groupindex in self.__groups:
                print "{0:>10s}".format( groupindex ),
            print
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
                            print "{0:6.3f}".format( correlations[ii] ),
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
        if self.__correlations is None:
            return None
        else:
            return dict( self.__correlations )
    def getCovariances( self ):
        return dict( self.__hcov )
    def getTotalCovariance( self ):
        return self.__cov.copy()
    def getGroups( self ):
        return list( self.__groups )
    def getGroupMatrix( self ):
        return list( self.__groupmatrix )
    def getSysterrorMatrix( self ):
        return dict( self.__systerrormatrix )
    def getReducedCovariances( self ):
        return dict( self.__hredcov )
    def getTotalReducedCovariance( self ):
        return self.__redcov.copy()
    def getTotalReducedCovarianceAslist( self ):
        return self.__redcov.tolist()

