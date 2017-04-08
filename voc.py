import hidapi


class Voc():

    def __init__(self):
        self.seq1 = 0x0001
        self.seq2 = 0x0068
        self.handle = None

        # Setup Device
        hidapi.hid_init()
        for dev in hidapi.hid_enumerate(vendor_id=0x03eb, product_id=0x2013):
            self.handle = hidapi.hid_open_path(dev.path)

        self.tx_type1(self.handle, '*IDN?')
        self.info = self.rx(self.handle)

    def version(self):
        import array
        return str("" + array.array('B', self.info).tostring() + "")

    def shutdown(self):
        hidapi.hid_close(self.handle)
        hidapi.hid_exit()

    def to_bytes(self, n, length, endianess='big'):
        h = '%x' % n
        s = ('0' * (len(h) % 2) + h).zfill(length * 2).decode('hex')
        return s if endianess == 'big' else s[::-1]

    def from_bytes(self, bytes, byteorder='little'):
        if byteorder == 'little':
            little_ordered = list(bytes)
        elif byteorder == 'big':
            little_ordered = list(reversed(bytes))

        n = sum(little_ordered[i] << i * 8 for i in range(len(little_ordered)))

        return n

    def tx_type1(self, handle, msg):
        msg = bytes('@{:04X}{}\n@@@@@@@@@@'.format(self.seq1, msg))
        hidapi.hid_write(handle, msg)

    def tx_type2(self, handle, msg):
        msg = bytes('@') + self.to_bytes(self.seq2, 1) + bytes('{}\n@@@@@@@@@@@@@'.format(msg))
        hidapi.hid_write(handle, msg)

    def rx(self, handle, numBytes=0x10):
        in_data = bytes()
        while True:
            ret = hidapi.hid_read_timeout(handle, numBytes, 1000)
            if len(ret) == 0:
                break
            in_data += ret

        return in_data

    def getPpm(self):
        self.tx_type2(self.handle, '*TR')
        data = self.rx(self.handle)

        return self.from_bytes(data[2:4])
