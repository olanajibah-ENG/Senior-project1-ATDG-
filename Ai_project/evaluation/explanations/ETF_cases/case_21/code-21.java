@SafeVarargs
    public final StreamEx<T> ifEmpty(T... values) {
        return ifEmpty(null, Spliterators.spliterator(values, Spliterator.ORDERED));
    }