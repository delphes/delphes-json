
/** \class ExRootConfReader
 *
 *  Class handling configuration data
 *
 *  \author P. Demin - UCL, Louvain-la-Neuve
 *
 */

#include "ExRootAnalysis/ExRootConfReader.h"

#include <fstream>
#include <sstream>
#include <stdexcept>

#include "cJSON/cJSON.h"
#include "cJSON/cJSON_Utils.h"

using namespace std;

//------------------------------------------------------------------------------

ExRootConfReader::ExRootConfReader()
{
}

//------------------------------------------------------------------------------

ExRootConfReader::~ExRootConfReader()
{
  if(fData) cJSON_Delete(fData);
}

//------------------------------------------------------------------------------

void ExRootConfReader::ReadData(const char *data)
{
  stringstream message;
  fData = cJSON_Parse(data);
  if(!fData)
  {
    message << "can't read configuration data";
    throw runtime_error(message.str());
  }
}

//------------------------------------------------------------------------------

void ExRootConfReader::ReadFile(const char *fileName)
{
  stringstream message;
  int length;
  char *buffer;

  ifstream inputFileStream(fileName, ios::in | ios::ate);
  if(!inputFileStream.is_open())
  {
    message << "can't open configuration file " << fileName;
    throw runtime_error(message.str());
  }

  length = inputFileStream.tellg();
  inputFileStream.seekg(0, ios::beg);
  inputFileStream.clear();
  buffer = new char[length + 1];
  buffer[length] = 0;
  inputFileStream.read(buffer, length);

  fData = cJSON_Parse(buffer);
  if(!fData)
  {
    message << "can't read configuration file " << fileName;
    throw runtime_error(message.str());
  }

  delete[] buffer;
}

//------------------------------------------------------------------------------

ExRootConfParam ExRootConfReader::GetParam(const char *name)
{
  return ExRootConfParam(name, cJSONUtils_GetPointerCaseSensitive(fData, name));
}

//------------------------------------------------------------------------------

int ExRootConfReader::GetInt(const char *name, int defaultValue, int index)
{
  ExRootConfParam object = GetParam(name);
  if(index >= 0)
  {
    object = object[index];
  }

  return object.GetInt(defaultValue);
}

//------------------------------------------------------------------------------

long ExRootConfReader::GetLong(const char *name, long defaultValue, int index)
{
  ExRootConfParam object = GetParam(name);
  if(index >= 0)
  {
    object = object[index];
  }

  return object.GetLong(defaultValue);
}

//------------------------------------------------------------------------------

double ExRootConfReader::GetDouble(const char *name, double defaultValue, int index)
{
  ExRootConfParam object = GetParam(name);
  if(index >= 0)
  {
    object = object[index];
  }

  return object.GetDouble(defaultValue);
}

//------------------------------------------------------------------------------

bool ExRootConfReader::GetBool(const char *name, bool defaultValue, int index)
{
  ExRootConfParam object = GetParam(name);
  if(index >= 0)
  {
    object = object[index];
  }

  return object.GetBool(defaultValue);
}

//------------------------------------------------------------------------------

const char *ExRootConfReader::GetString(const char *name, const char *defaultValue, int index)
{
  ExRootConfParam object = GetParam(name);
  if(index >= 0)
  {
    object = object[index];
  }

  return object.GetString(defaultValue);
}

//------------------------------------------------------------------------------

ExRootConfParam::ExRootConfParam(const char *name, cJSON *data) :
  TNamed(name, ""), fData(data)
{
}

//------------------------------------------------------------------------------

int ExRootConfParam::GetInt(int defaultValue)
{
  return GetDouble(defaultValue);
}

//------------------------------------------------------------------------------

long ExRootConfParam::GetLong(long defaultValue)
{
  return GetDouble(defaultValue);
}

//------------------------------------------------------------------------------

double ExRootConfParam::GetDouble(double defaultValue)
{
  stringstream message;

  if(!fData) return defaultValue;

  if(cJSON_IsNumber(fData)) return cJSON_GetNumberValue(fData);

  message << "parameter '" << GetName() << "' is not a number." << endl;
  message << GetName() << " = " << cJSON_Print(fData);
  throw runtime_error(message.str());
}

//------------------------------------------------------------------------------

bool ExRootConfParam::GetBool(bool defaultValue)
{
  stringstream message;

  if(!fData) return defaultValue;

  if(cJSON_IsBool(fData)) return cJSON_IsTrue(fData);

  if(cJSON_IsNumber(fData)) return cJSON_GetNumberValue(fData);

  message << "parameter '" << GetName() << "' is not a boolean." << endl;
  message << GetName() << " = " << cJSON_Print(fData);
  throw runtime_error(message.str());
}

//------------------------------------------------------------------------------

const char *ExRootConfParam::GetString(const char *defaultValue)
{
  stringstream message;

  if(!fData) return defaultValue;

  if(cJSON_IsString(fData)) return cJSON_GetStringValue(fData);

  return cJSON_Print(fData);
}

//------------------------------------------------------------------------------

int ExRootConfParam::GetSize()
{
  if(!fData) return 0;

  if(cJSON_IsArray(fData)) return cJSON_GetArraySize(fData);

  return 1;
}

//------------------------------------------------------------------------------

ExRootConfParam ExRootConfParam::operator[](int index)
{
  if(!fData) ExRootConfParam(GetName(), fData);

  if(cJSON_IsArray(fData)) return ExRootConfParam(GetName(), cJSON_GetArrayItem(fData, index));

  return ExRootConfParam(GetName(), fData);
}
