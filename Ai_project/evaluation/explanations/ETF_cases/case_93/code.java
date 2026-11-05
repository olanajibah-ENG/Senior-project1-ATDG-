public SwimMembershipProtocolConfig setFailureTimeout(Duration failureTimeout) {
    checkNotNull(failureTimeout, "failureTimeout cannot be null");
    checkArgument(!failureTimeout.isNegative() && !failureTimeout.isZero(), "failureTimeout must be positive");
    this.failureTimeout = checkNotNull(failureTimeout);
    return this;
  }