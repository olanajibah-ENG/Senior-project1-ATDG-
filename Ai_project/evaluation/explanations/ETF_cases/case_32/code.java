public static HashSet<String> createSetFromProperty(String property)
	{
		HashSet<String> properties = new HashSet<String>();

		if (property != null && !property.equals("null")) {
			\/\/ "([\\w]*)=([\\w]*);"
			Pattern params = Pattern.compile("([\\w]+)[;]*");
			Matcher matcher = params.matcher(property.trim());
			while (matcher.find()) {
				properties.add(matcher.group(1));
			}

		}

		return properties;
	}