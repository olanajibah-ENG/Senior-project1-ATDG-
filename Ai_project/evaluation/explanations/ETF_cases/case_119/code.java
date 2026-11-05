private void handleTimeoutError(Status status) {
    Preconditions.checkArgument(status.getCause() instanceof StreamWaitTimeoutException,
        "status is not caused by a StreamWaitTimeoutException");
    StreamWaitTimeoutException e = ((StreamWaitTimeoutException) status.getCause());

    \/\/ Cancel the existing rpc.
    rpcTimerContext.close();
    failedCount++;

    \/\/ Can this request be retried
    int maxRetries = retryOptions.getMaxScanTimeoutRetries();
    if (retryOptions.enableRetries() && ++timeoutRetryCount <= maxRetries) {
      LOG.warn("The client could not get a response in %d ms. Retrying the scan.",
          e.getWaitTimeMs());

      resetStatusBasedBackoff();
      performRetry(0);
    } else {
      LOG.warn("The client could not get a response after %d tries, giving up.",
          timeoutRetryCount);
      rpc.getRpcMetrics().markFailure();
      finalizeStats(status);
      setException(getExhaustedRetriesException(status));
    }
  }