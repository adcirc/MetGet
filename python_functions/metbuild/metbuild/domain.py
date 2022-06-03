class Domain:
    def __init__(self, name, service, json):
        from metbuild.windgrid import WindGrid
        self.__name = name
        self.__service = service
        self.__json = json
        self.__grid = WindGrid(self.__json)
        self.__storm = None
        self.__valid = True
        self.__get_storm()

    def storm(self):
        return self.__storm

    def name(self):
        return self.__name

    def service(self):
        return self.__service

    def grid(self):
        return self.__grid

    def json(self):
        return self.__json

    def __get_storm(self):
        if self.service() == "hwrf" or self.service() == "coamps-tc":
            if "storm" in self.__json:
                self.__storm = self.__json["storm"]
            else: 
                self.__valid = False
        else:
            self.__storm = None

