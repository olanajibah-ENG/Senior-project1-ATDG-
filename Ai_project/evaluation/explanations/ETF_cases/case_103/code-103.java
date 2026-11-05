private static void checkIsValidH2Header(H2HeaderField header, boolean isTrailerField) throws CompressionException {
        if (!header.getName().startsWith(":")) {
            String headerName = header.getName();
            String headerValue = header.getValue();

            for (String name : HpackConstants.connectionSpecificHeaderList) {
                if (name.equalsIgnoreCase(headerName)) {
                    throw new CompressionException("Invalid Connection header received: " + header.toString());
                }
            }
            if ("Connection".equalsIgnoreCase(headerName) && !"TE".equalsIgnoreCase(headerValue)) {
                throw new CompressionException("Invalid Connection header received: " + header.toString());
            }
            if ("TE".equalsIgnoreCase(headerName) && !"trailers".equalsIgnoreCase(headerValue)) {
                throw new CompressionException("Invalid header: TE header must have value \"trailers\": " + header.toString());
            }
        } else {
            if (isTrailerField) {
                throw new CompressionException("Psuedo-headers are not allowed in trailers: " + header.toString());
            }
        }
    }