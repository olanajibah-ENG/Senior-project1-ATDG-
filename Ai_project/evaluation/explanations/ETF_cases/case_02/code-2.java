public RowBuilder int16(String name)
  {
    ColumnInt16 column = new ColumnInt16(_columns.size(), name, _offset);
    
    _offset += column.length();
    _columns.add(column);
    
    return this;
  }
