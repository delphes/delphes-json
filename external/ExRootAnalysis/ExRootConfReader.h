#ifndef ExRootConfReader_h
#define ExRootConfReader_h

/** \class ExRootConfReader
 *
 *  Class configuration data
 *
 *  \author P. Demin - UCL, Louvain-la-Neuve
 *
 */

#include "TNamed.h"

struct cJSON;

class ExRootConfParam: public TNamed
{
public:
  ExRootConfParam(const char *name = 0, cJSON *data = 0);

  int GetInt(int defaultValue = 0);
  long GetLong(long defaultValue = 0);
  double GetDouble(double defaultValue = 0.0);
  bool GetBool(bool defaultValue = false);
  const char *GetString(const char *defaultValue = "");

  int GetSize();
  ExRootConfParam operator[](int index);

private:
  cJSON *fData = nullptr; //!

  ClassDef(ExRootConfParam, 1)
};

//------------------------------------------------------------------------------

class ExRootConfReader: public TNamed
{
public:
  ExRootConfReader();
  ~ExRootConfReader();

  void ReadData(const char *data);
  void ReadFile(const char *fileName);

  int GetInt(const char *name, int defaultValue, int index = -1);
  long GetLong(const char *name, long defaultValue, int index = -1);
  double GetDouble(const char *name, double defaultValue, int index = -1);
  bool GetBool(const char *name, bool defaultValue, int index = -1);
  const char *GetString(const char *name, const char *defaultValue, int index = -1);
  ExRootConfParam GetParam(const char *name);

private:
  cJSON *fData = nullptr; //!

  ClassDef(ExRootConfReader, 1)
};

#endif
