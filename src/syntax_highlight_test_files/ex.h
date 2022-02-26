#pragma once

#include <string>

/**
 * GPS coordination representation.
 */
class GPS {
public:
	GPS();

	/**
	 * parse and construct GPS coordination.
	 * Expected format:
	 * HH°MM'SS.SS"{N,S},HH°MM'SS.SS"{E,W}
	 */
	GPS(std::string gpsStr);

	GPS(double latitude, double longitude);

	void print();

	bool operator==(const GPS other);

	double m_latitude;
	double m_longitude;
};
