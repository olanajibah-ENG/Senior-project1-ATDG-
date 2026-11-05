public static SystemMain getInstance(Properties config) {
        return Guice.createInjector(new SystemInitializer(config)).getInstance(SystemMain.class);
    }