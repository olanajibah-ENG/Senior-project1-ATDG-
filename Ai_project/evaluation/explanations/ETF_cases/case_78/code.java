public int getLength()
	{
		int length = 0;

		Iterator<V> it = this.values().iterator();
		while (it.hasNext())
		{
			length += ((ID3v2Frame) it.next()).getFrameLength();
		}

		return length;
	}