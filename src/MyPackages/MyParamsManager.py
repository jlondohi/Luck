import json
from functools import partial
from collections import OrderedDict

from PyQt6.QtWidgets import (QLayout, QWidget, QStyleOption, QStyle
                             , QMenu, QApplication)
from PyQt6.QtCore import QRect, QSize, Qt, QPoint
from PyQt6.QtGui import QPainter, QAction

#====================================================================
### Creating a custom QWidget class
#====================================================================
class LimitedDict(OrderedDict):
    """
    Ordered dictionary with a maximum length. Removes the oldest item when the limit is exceeded.

    Attributes:
        maxlen (int): Maximum number of items allowed in the dictionary.

    Methods:
        __setitem__(self, key, value, *args): Sets an item, removing the oldest if necessary.
        clear(self, *args): Clears the dictionary.
    """
    def __init__(self, maxlen):
        """
        Initializes the LimitedDict with a maximum length.

        Args:
            maxlen (int): Maximum number of items allowed.
        """
        super().__init__()
        self.maxlen = maxlen

    def __setitem__(self, key, value, *args):
        """
        Sets an item in the dictionary, removing the oldest if the limit is reached.

        Args:
            key: The key to set.
            value: The value to set.
            *args: Additional arguments (unused).
        """
        #If it already exists, eliminate it to put it last
        if key in self:
            del self[key]
        #If the limit was reached, eliminate the oldest
        elif len(self) >= self.maxlen:
            #Eliminates the first inserted
            self.popitem(last=False) 
        super().__setitem__(key, value)
    
    def clear(self, *args):
        """
        Clears all items from the dictionary.

        Args:
            *args: Additional arguments (unused).
        """
        super().clear()

class MyParamsManager(QWidget):
    """
    Custom QWidget for managing parameters with context menu actions and parameter memory.

    Attributes:
        parent (QWidget): Parent widget.
        i18nNes (callable): Internationalization function.
        contextMenu (QMenu): Context menu for parameter actions.
        parameterBag (LimitedDict): Memory for storing parameters.

    Methods:
        __init__(self, parent=None): Initializes the parameter manager.
        paintEvent(self, event, *args): Handles the paint event for custom drawing.
        createMenu(self, *args): Creates the context menu for parameter actions.
        showMenu(self, position, *args): Shows the context menu at the given position.
        actionCopy(self, *args): Copies current parameters to the clipboard.
        actionPaste(self, *args): Pastes parameters from the clipboard.
        actionDelAll(self, *args): Clears all current parameters.
        actionDelBag(self, *args): Clears the parameter memory bag.
    """
    def __init__(self, parent=None):
        """
        Initializes the parameter manager widget.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.parent = parent
        self.i18nNes = parent.i18nNes
        #Creating contextMenu
        self.contextMenu = self.createMenu()
        #Enable the personalized context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showMenu)
        #Parameter memory
        maxlen = self.parent.cfg_app.index.get('max-param-memory', 50)
        self.parameterBag = LimitedDict(maxlen=maxlen)
    
    def paintEvent(self, event, *args):
        """
        Handles the paint event for custom widget drawing.

        Args:
            event (QPaintEvent): The paint event.
            *args: Additional arguments (unused).
        """
        super().paintEvent(event)
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)
    
    #Creatin menu
    def createMenu(self, *args):
        """
        Creates the context menu for parameter actions.

        Args:
            *args: Additional arguments (unused).

        Returns:
            QMenu: The created context menu.
        """
        menu = QMenu(self)
        #Creating actions
        names = self.i18nNes('tab-paramsManager')
        actionCopy      = QAction(names['copy'], self)
        actionPaste     = QAction(names['paste'], self)
        actionDelAll    = QAction(names['del-all'], self)
        actionDelBag    = QAction(names['del-bag'], self)
        actionOpen      = QAction(names['open'], self)
        actionSave      = QAction(names['save'], self)
        actionSaveAss   = QAction(names['save-ass'], self)
        
        #Connecting actions
        actionCopy.triggered.connect(self.actionCopy)
        actionPaste.triggered.connect(self.actionPaste)
        actionDelAll.triggered.connect(self.actionDelAll)
        actionDelBag.triggered.connect(self.actionDelBag)
        actionOpen.triggered.connect(partial(self.parent.openFileP, True))
        actionSave.triggered.connect(partial(self.parent.savingChangesP, '', 'save'))
        actionSaveAss.triggered.connect(partial(self.parent.savingChangesP, '', 'saveAs'))

        #Adding actions to the menu
        menu.addAction(actionCopy)
        menu.addAction(actionPaste)
        menu.addSeparator()
        menu.addAction(actionDelAll)
        menu.addAction(actionDelBag)
        menu.addSeparator()
        menu.addAction(actionOpen)
        menu.addAction(actionSaveAss)
        return menu
            
    #Function to detect request of context menú
    def showMenu(self, position, *args):
        """
        Shows the context menu at the specified position.

        Args:
            position (QPoint): The position to show the menu.
            *args: Additional arguments (unused).
        """
        self.contextMenu.exec(self.mapToGlobal(position))
    
    #Function linked to the copy action
    def actionCopy(self, *args):
        """
        Copies the current parameters to the clipboard in JSON format.

        Args:
            *args: Additional arguments (unused).
        """
        params = self.parent.current_paramsEtl
        txt_json = json.dumps(params)
        QApplication.clipboard().setText(txt_json)
    
    #Function linked to the paste action
    def actionPaste(self, *args):
        """
        Pastes parameters from the clipboard and updates the current parameters.

        Args:
            *args: Additional arguments (unused).
        """
        txt_json = QApplication.clipboard().text()
        try:
            params = json.loads(txt_json)
        except json.JSONDecodeError:
            return

        params = {**self.parent.current_paramsEtl, **params}
        #Getting the name of the current tab
        tab_name = self.parent.tabWidget.currentWidget().objectName
        tab_data = self.parent.tabInfo.get(tab_name)
        if tab_data:
            tab_data['dict_paramsEtl'] = params
        #Updating visualizer
        self.parent.current_paramsEtl = params
        self.parent.updatePManager()

    #Function linked to the del-all action
    def actionDelAll(self, *args):
        """
        Clears all current parameters and updates the parameter manager.

        Args:
            *args: Additional arguments (unused).
        """
        for key in self.parent.current_paramsEtl.keys():  
            self.parent.current_paramsEtl[key] = ''

        #Getting the name of the current tab
        tab_name = self.parent.tabWidget.currentWidget().objectName
        tab_data = self.parent.tabInfo.get(tab_name)
        if tab_data:
            tab_data['dict_paramsEtl'] = self.parent.current_paramsEtl
        #Erasing parameter memory
        self.parameterBag.clear()
        #Erasing widget parameters
        self.parent.updatePManager()
    
    #Function linked to the del-bag action
    def actionDelBag(self, *args):
        """
        Clears the parameter memory bag.

        Args:
            *args: Additional arguments (unused).
        """
        self.parameterBag.clear()

#====================================================================
### Creating a custom QLayout class to organize the parameter manager
#====================================================================
class MyFlowLayout(QLayout):
    """
    Custom QLayout for arranging widgets in a flowing layout, similar to text wrapping.

    Attributes:
        itemList (list): List of layout items.

    Methods:
        __init__(self, parent=None, margin=1, spacing=1): Initializes the flow layout.
        addItem(self, item): Adds an item to the layout.
        count(self): Returns the number of items in the layout.
        itemAt(self, index): Returns the item at the given index.
        takeAt(self, index): Removes and returns the item at the given index.
        expandingDirections(self): Returns the directions the layout can expand.
        hasHeightForWidth(self): Returns True if the layout prefers height for width.
        heightForWidth(self, width): Returns the preferred height for the given width.
        setGeometry(self, rect): Sets the geometry of the layout.
        sizeHint(self): Returns the recommended size for the layout.
        minimumSize(self): Returns the minimum size for the layout.
        doLayout(self, rect, testOnly): Arranges the items within the given rectangle.
    """
    def __init__(self, parent=None, margin=1, spacing=1):
        """
        Initializes the flow layout.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
            margin (int, optional): Margin size. Defaults to 1.
            spacing (int, optional): Spacing between items. Defaults to 1.
        """
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []
    
    def addItem(self, item):
        """
        Adds an item to the layout.

        Args:
            item (QLayoutItem): The item to add.
        """
        self.itemList.append(item)

    def count(self):
        """
        Returns the number of items in the layout.

        Returns:
            int: Number of items.
        """
        return len(self.itemList)

    def itemAt(self, index):
        """
        Returns the item at the specified index.

        Args:
            index (int): Index of the item.

        Returns:
            QLayoutItem or None: The item at the index, or None if out of range.
        """
        return self.itemList[index] if index < len(self.itemList) else None

    def takeAt(self, index):
        """
        Removes and returns the item at the specified index.

        Args:
            index (int): Index of the item.

        Returns:
            QLayoutItem or None: The removed item, or None if out of range.
        """
        return self.itemList.pop(index) if index < len(self.itemList) else None

    def expandingDirections(self):
        """
        Returns the directions the layout can expand.

        Returns:
            Qt.Orientations: The expanding directions.
        """
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        """
        Returns whether the layout prefers height for width.

        Returns:
            bool: True if height for width is preferred.
        """
        return True

    def heightForWidth(self, width):
        """
        Returns the preferred height for the given width.

        Args:
            width (int): The width to calculate height for.

        Returns:
            int: The preferred height.
        """
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        """
        Sets the geometry of the layout.

        Args:
            rect (QRect): The rectangle to set the layout geometry to.
        """
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        """
        Returns the recommended size for the layout.

        Returns:
            QSize: The recommended size.
        """
        return self.minimumSize()

    def minimumSize(self):
        """
        Returns the minimum size for the layout.

        Returns:
            QSize: The minimum size.
        """
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def doLayout(self, rect, testOnly):
        """
        Arranges the items within the given rectangle.

        Args:
            rect (QRect): The rectangle to arrange items in.
            testOnly (bool): If True, only calculates layout without setting geometry.

        Returns:
            int: The total height used by the layout.
        """
        x, y, lineHeight = rect.x(), rect.y(), 0
        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing()
            spaceY = self.spacing()
            nextX = x + wid.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + wid.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), wid.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, wid.sizeHint().height())

        return y + lineHeight - rect.y()