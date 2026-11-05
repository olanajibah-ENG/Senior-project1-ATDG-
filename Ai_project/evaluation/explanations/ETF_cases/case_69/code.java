public void logProperties(final Logger logger, final String comment) {
    logger.info(comment);

    for (final String key : getKeySet()) {
      logger.info("  key=" + key + " value=" + get(key));
    }
  }