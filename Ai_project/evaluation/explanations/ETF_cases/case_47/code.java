private void computeIv(long label, long index) {
		long key_id;

		if (keyDerivationRate == 0) {
			key_id = label << 48;
		} else {
			key_id = ((label << 48) | (index \/ keyDerivationRate));
		}
		for (int i = 0; i < 7; i++) {
			ivStore[i] = masterSalt[i];
		}
		for (int i = 7; i < 14; i++) {
			ivStore[i] = (byte) ((byte) (0xFF & (key_id >> (8 * (13 - i)))) ^ masterSalt[i]);
		}
		ivStore[14] = ivStore[15] = 0;
	}