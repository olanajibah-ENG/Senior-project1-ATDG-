public SortedMap<String, HealthCheck.Result> runHealthChecks(HealthCheckFilter filter) {
        final SortedMap<String, HealthCheck.Result> results = new TreeMap<>();
        for (Map.Entry<String, HealthCheck> entry : healthChecks.entrySet()) {
            final String name = entry.getKey();
            final HealthCheck healthCheck = entry.getValue();
            if (filter.matches(name, healthCheck)) {
                final Result result = entry.getValue().execute();
                results.put(entry.getKey(), result);
            }
        }
        return Collections.unmodifiableSortedMap(results);
    }
