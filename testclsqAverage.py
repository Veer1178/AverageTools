#!/usr/bin/python

# unit tests for constrained least squares averages
# S. Kluth 01/2012

import unittest

import clsqAverage


class clsqAverageTest( unittest.TestCase ):

    def setUp( self ):
        self.__ca= clsqAverage.clsqAverage( "test.txt" )
        self.__ca.calcAverage()
        return

    def test_getAverage( self ):
        val, error= self.__ca.getAverage()
        expectedval= 170.709196921
        expectederror= 2.9668615985
        self.assertAlmostEqual( val, expectedval )
        self.assertAlmostEqual( error, expectederror )
        return

    def test_mpars( self ):
        solver= self.__ca.getSolver()
        mpar= solver.getMpar()
        mparerrors= solver.getMparErrors()
        expectedmpar= [ 171.51710348441537, 172.29268242120295, 
                        172.55882080482172, 
                        -0.24715555753633961, -0.41819040151052728 ]

        expectedmparerrors= [ 2.6568482263780098, 2.9263187806182231, 
                              3.1214377706098424, 
                              0.95849417709990359, 0.81760662703871312 ]
        for par, expectedpar in zip( mpar, expectedmpar ):
            self.assertAlmostEqual( par, expectedpar )
        for par, expectedpar in zip( mparerrors, expectedmparerrors ):
            self.assertAlmostEqual( par, expectedpar )
        return

    def test_fitpars( self ):
        solver= self.__ca.getSolver()
        chisq= solver.getChisq()
        ndof= solver.getNdof()
        expectedchisq= 0.77002509362026528
        expectedndof= 2
        self.assertAlmostEqual( chisq, expectedchisq )
        self.assertEqual( ndof, expectedndof )
        return

    def test_weights( self ):
        weightsMatrix= self.__ca.calcWeightsMatrix()
        weightsList= [ weight for weight in weightsMatrix.flat ]
        expectedWeights= [ 1.3390306603764943, 
                           -0.16163492965394771, 
                           -0.17739573072419634 ]
        for weight, expectedWeight in zip( weightsList, expectedWeights ):
            self.assertAlmostEqual( weight, expectedWeight )
        return


if __name__ == '__main__':
    suite= unittest.TestLoader().loadTestsFromTestCase( clsqAverageTest )
    unittest.TextTestRunner( verbosity=2 ).run( suite )

