"""Authenticated, bounded-memory archive framing. Sequence numbers prevent reorder."""
import io
import struct
from cryptography.fernet import Fernet

MAGIC = b'SECUREAI-BACKUP-1\n'
BLOCK = 1024 * 1024


class EncryptedWriter:
    def __init__(self, output, key):
        self.output=output
        self.cipher=Fernet(key.encode())
        self.sequence=0
        output.write(MAGIC)

    def write(self, data):
        for offset in range(0,len(data),BLOCK):
            token=self.cipher.encrypt(struct.pack('!Q',self.sequence)+b'D'+data[offset:offset+BLOCK])
            self.output.write(struct.pack('!I',len(token))+token)
            self.sequence+=1
        return len(data)

    def finish(self):
        token=self.cipher.encrypt(struct.pack('!Q',self.sequence)+b'E')
        self.output.write(struct.pack('!I',len(token))+token)


def decrypt_archive(source, destination, key):
    if source.read(len(MAGIC)) != MAGIC: raise ValueError('Invalid backup format')
    cipher=Fernet(key.encode())
    sequence=0
    while True:
        length=source.read(4)
        if len(length)!=4: raise ValueError('Truncated backup')
        size=struct.unpack('!I',length)[0]
        if size<64 or size>2*BLOCK: raise ValueError('Invalid backup frame')
        token=source.read(size)
        if len(token)!=size: raise ValueError('Truncated backup')
        data=cipher.decrypt(token)
        if len(data)<9 or struct.unpack('!Q',data[:8])[0]!=sequence: raise ValueError('Invalid frame order')
        if data[8:]==b'E':
            if source.read(1): raise ValueError('Unexpected trailing data')
            return
        if data[8:9]!=b'D': raise ValueError('Invalid frame type')
        destination.write(data[9:])
        sequence+=1


def pg_environment(database):
    import os
    env=dict(os.environ)
    env.update(PGHOST=str(database['HOST']),PGPORT=str(database['PORT']),PGDATABASE=database['NAME'],PGUSER=database['USER'],PGPASSWORD=database['PASSWORD'])
    options=database.get('OPTIONS',{})
    env['PGSSLMODE']=options.get('sslmode','prefer')
    if options.get('sslrootcert'): env['PGSSLROOTCERT']=options['sslrootcert']
    return env
