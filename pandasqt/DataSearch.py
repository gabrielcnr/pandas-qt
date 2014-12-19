# -*- coding: utf-8 -*-

import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

import parser
import re

import numpy as np
import pandas as pd

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

class DataSearch(object):
    """object which provides parsing functionality for a DataFrame.

    A `DataSearch` can apply custom filters defined as python expressions
    to a `pandas.DataFrame` object. The dataframe will evaluate the expressions
    and return a list with index which either match or fail the expression.

    Attributes:
        name (str): Each `DataSearch` object should have a name. The name could
            be used to store different `DataSearch` objects as predefined filters.

    """

    def __init__(self, name, filterString='', dataFrame=pd.DataFrame()):
        """Constructs a `DataSearch` object from the given attributes.

        Args:
            name (str): The name of the filter.
            filterString (str, optional): A python expression as string.
                Defaults to an empty string.
            dataFrame (pandas.DataFrame, optional): The object to filter.
                Defaults to an empty `DataFrame`.

        """
        self._filterString = filterString
        self._dataFrame = dataFrame
        self.name = name

    def __repr__(self):
        string = u"DataSearch({}): {} ({})".format(hex(id(self)), self.name, self._filterString)
        string = string.encode("utf-8")
        return string

    def dataFrame(self):
        """Getter method for the `dataFrame` attribute.

        Note:
            It's not implemented with python properties to keep Qt conventions.

        Returns:
            pandas.DataFrame: A `DataFrame` object.

        """
        return self._dataFrame

    def setDataFrame(self, dataFrame):
        """Updates/sets the dataFrame attribute of this class.

        Args:
            dataFrame (pandas.DataFrame): The new `dataFrame` object.

        """
        self._dataFrame = dataFrame

    def filterString(self):
        """Getter method for the `filterString` attribute.

        Note:
            It's not implemented with python properties to keep Qt conventions.

        Returns:
            str: the filter/python expression as string.

        """
        return self._filterString

    def setFilterString(self, filterString):
        """Updates/sets the filterString attribute of this class.

        Args:
            filterString (str): A python expression as string. All leading and
                trailing spaces will be removed.

        """
        ## remove leading whitespaces, they will raise an identation error
        filterString = filterString.strip()
        self._filterString = filterString

    def search(self):
        """Applies the filter to the stored dataframe.

        A safe environment dictionary will be created, which stores all allowed
        functions and attributes, which may be used for the filter.
        If any object in the given `filterString` could not be found in the
        dictionary, the filter does not apply and returns `False`.

        Returns:
            tuple: A (indexes, success)-tuple, which indicates identified objects
                by applying the filter and if the operation was successful in
                general.

        """
        # there should be a grammar defined and some lexer/parser.
        # instead of this quick-and-dirty implementation.

        safeEnvDict = {
            'freeSearch': self.freeSearch,
            'extentSearch': self.extentSearch,
            'indexSearch': self.indexSearch

        }
        for col in self._dataFrame.columns:
            safeEnvDict[col] = self._dataFrame[col]

        try:
            searchIndex = eval(self._filterString, {'__builtins__': None}, safeEnvDict)
        except NameError as err:
            return [], False
        except SyntaxError as err:
            return [], False
        except ValueError as err:
            # the use of 'and'/'or' is not valid, need to use binary operators.
            return [], False
        except TypeError as err:
            # argument must be string or compiled pattern
            return [], False
        return searchIndex, True

    def freeSearch(self, searchString):
        """Execute a free text search for all columns in the dataframe.

        Args:
            searchString (str): Any string which may be contained in any column.

        Returns:
            list: A list containing all indexes with filtered data. Matches will
                be `True`, the remaining items will be `False`. If the dataFrame
                is empty, an empty list will be returned.

        """

        if not self._dataFrame.empty:
            # set question to the indexes of data and set everything to false.
            question = self._dataFrame.index == -9999
            for column in self._dataFrame.columns:
                dfColumn = self._dataFrame[column]
                dfColumn = dfColumn.apply(unicode)

                question2 = dfColumn.str.contains(searchString, flags=re.IGNORECASE, regex=True, na=False)
                question = np.logical_or(question, question2)

            return question
        else:
            return []

    def extentSearch(self, xmin, ymin, xmax, ymax):
        """Filters the data by a geographical bounding box.

        The bounding box is given as lower left point coordinates and upper
        right point coordinates.

        Note:
            It's necessary that the dataframe has a `lat` and `lng` column
            in order to apply the filter.

            Check if the method could be removed in the future. (could be done
            via freeSearch)

        Returns:
            list: A list containing all indexes with filtered data. Matches will
                be `True`, the remaining items will be `False`. If the dataFrame
                is empty, an empty list will be returned.

        """
        if not self._dataFrame.empty:
            try:
                questionMin = (self._dataFrame.lat >= xmin) & (self._dataFrame.lng >= ymin)
                questionMax = (self._dataFrame.lat <= xmax) & (self._dataFrame.lng <= ymax)
                return np.logical_and(questionMin, questionMax)
            except AttributeError:
                return []
        else:
            return []

    def indexSearch(self, indexes):
        """Filters the data by a list of indexes.

        Returns:
            list: A list containing all indexes with filtered data. Matches will
                be `True`, the remaining items will be `False`. If the dataFrame
                is empty, an empty list will be returned.

        """
        if not self._dataFrame.empty:
            filter0 = self._dataFrame.index == -9999
            for index in indexes:
                filter1 = self._dataFrame.index == index
                filter0 = np.logical_or(filter0, filter1)

            return filter0
        else:
            return []

    #def applySearch(self):
        #filterCondition = self.search()
        #resultingIndexes = self.table.dataFrame[filterCondition].index
        #resultingIndexesString = str(list(resultingIndexes)).replace('[', '(').replace(']', ')')
        #subsetString = u'"index" IN {0}'.format(resultingIndexesString)
        ##print subsetString

        ### apply filter if we have an active sql model
        ##print self.table.sqlDataFrameModel
        #if self.table.sqlDataFrameModel:
            #self.table.sqlDataFrameModel.setFilter(subsetString)

        ### apply filter to qgis vector layer, even if this is empty
        #if list(resultingIndexes) == []:
            #subsetString = u'"index" >= 0'
        #else:
            #subsetString = u'"index" IN {0}'.format(resultingIndexesString)
        #self.table.pointLayer.setSubsetString(subsetString)
        ##print "set filter to point layer", self.table.pointLayer, self.table.pointLayer.featureCount()
        ##print self.table.pointLayer.subsetString()

        #return filterCondition