public static void assertRequiredContainerTriples(final Model model)
            throws ConstraintViolationException {
        assertContainsRequiredProperties(model, REQUIRED_PROPERTIES);
        assertContainsRequiredTypes(model, CONTAINER_TYPES);
    }