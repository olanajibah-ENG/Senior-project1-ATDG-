public MockVolume createVolume(
            final String volumeType, final String size, final String availabilityZone,
            final int iops,
            final String snapshotId) {

        MockVolume ret = new MockVolume();
        ret.setVolumeType(volumeType);
        ret.setVolumeId(
                "vol-" + UUID.randomUUID().toString().substring(0, VOLUME_ID_POSTFIX_LENGTH));
        ret.setSize(size);
        ret.setAvailabilityZone(availabilityZone);
        ret.setIops(iops);
        ret.setSnapshotId(snapshotId);

        allMockVolumes.put(ret.getVolumeId(), ret);
        return ret;
    }