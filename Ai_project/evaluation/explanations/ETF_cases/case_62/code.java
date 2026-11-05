public void flush() throws IOException {
    \/\/ check if the stream has been closed
    checkError();
    
    \/\/ how many bytes were written to the buffer
    long totalBytesWritten = buffer.totalWritten();
    
    \/\/ unblock reads from the buffer
    buffer.unblockReads();
    
    \/\/ wait until the write thread transfers everything from the
    \/\/ buffer to the stream
    while (writeThread.totalBytesTransferred < totalBytesWritten) {
      BufferedByteInputOutput.sleep(1);
    }
    
    InjectionHandler.processEvent(
        InjectionEventCore.BUFFEREDBYTEOUTPUTSTREAM_FLUSH,
        writeThread.totalBytesTransferred);
    
    \/\/ check error
    checkError();
    
    \/\/ block reads
    buffer.blockReads();
    
    \/\/ flush the underlying buffer
    underlyingOutputStream.flush();
  }