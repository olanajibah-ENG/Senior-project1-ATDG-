@Override
    public DateCalculator<E> setStartDate(final E startDate) {
        this.startDate = startDate;
        setCurrentBusinessDate(startDate);
        return this;
    }