class HRVAnalyzer:
    @staticmethod
    def meanPPI_calculator(data):
        """
        Calculates the mean PPI (Pulse-to-Pulse Interval) from the given data.
        """
        sumPPI = sum(data)
        return int(round(sumPPI / len(data), 0))

    @staticmethod
    def SDNN_calculator(data, PPI):
        """
        Calculates the Standard Deviation of NN intervals (SDNN) from the given data.
        """
        summary = sum((i - PPI) ** 2 for i in data)
        return int(round((summary / (len(data) - 1)) ** 0.5, 0))

    @staticmethod
    def RMSSD_calculator(data):
        """
        Calculates the Root Mean Square of Successive Differences (RMSSD) from the given data.
        """
        summary = sum((data[i + 1] - data[i]) ** 2 for i in range(len(data) - 1))
        return int(round((summary / (len(data) - 1)) ** 0.5, 0))