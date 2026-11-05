public List<String> getMetaKeywordsForModule(ModuleElement mdle) {
        if (config.keywords) {
            return Arrays.asList(mdle.getQualifiedName() + " " + "module");
        } else {
            return Collections.emptyList();
        }
    }