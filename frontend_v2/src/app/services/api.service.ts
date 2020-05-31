import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { GlobalService } from './global.service';

@Injectable()
export class ApiService {
  API = environment.api_endpoint;
  HEADERS = { 'Content-Type': 'application/json' };
  HTTP_OPTIONS: any;

  /**
   * Constructor.
   * @param http  Http Injection.
   * @param globalService  GlobalService Injection.
   */
  constructor(private http: HttpClient, private globalService: GlobalService) { }

  /**
   * Prepares headers for each request to API.
   * @param fileHeaders  Set to true when uploading a file.
   */
  prepareHttpOptions(fileHeaders = false) {
    const TOKEN = this.globalService.getAuthToken();
    if (TOKEN) {
      this.HEADERS['Authorization'] = 'Token ' + TOKEN;
    } else {
      delete this.HEADERS['Authorization'];
    }
    const TEMP = Object.assign({}, this.HEADERS);
    if (fileHeaders) {
      delete TEMP['Content-Type'];
    }
    this.HTTP_OPTIONS = {
      headers: new HttpHeaders(TEMP)
    };
    return TEMP;
  }

  /**
   * HTTP GET wrapper.
   * @param path  path of API call.
   * @param isJson  set to false when fetching some non-JSON content.
   */
  getUrl(path: string, isJson = true, isLoader = true) {
    if (isJson) {
      this.prepareHttpOptions();
      return this.loadingWrapper(this.http.get(this.API + path, this.HTTP_OPTIONS), isLoader);
    } else {
      this.prepareHttpOptions(true);
      const TEMP = Object.assign({}, this.HTTP_OPTIONS, { observe: 'response', responseType: 'text' });
      return this.loadingWrapper(this.http.get(this.API + path, TEMP));
    }
  }

  /**
   * HTTP POST wrapper.
   * @param path  path of API call.
   * @param body  stringified json body.
   */
  postUrl(path: string, body: any) {
    this.prepareHttpOptions();
    return this.loadingWrapper(this.http.post(this.API + path, body, this.HTTP_OPTIONS));
  }

  /**
   * HTTP PATCH wrapper.
   * @param path  path of API call.
   * @param body  stringified json body.
   */
  patchUrl(path: string, body: any) {
    this.prepareHttpOptions();
    return this.loadingWrapper(this.http.patch(this.API + path, body, this.HTTP_OPTIONS));
  }

  /**
   * HTTP PUT wrapper.
   * @param path  path of API call.
   * @param body  stringified json body.
   */
  putUrl(path: string, body: any) {
    this.prepareHttpOptions();
    return this.loadingWrapper(this.http.put(this.API + path, body, this.HTTP_OPTIONS));
  }

  /**
   * HTTP POST (file upload) wrapper.
   * @param path  path of API call.
   * @param body  stringified json body.
   */
  postFileUrl(path: string, formData: any) {
    this.prepareHttpOptions(true);
    return this.loadingWrapper(this.http.post(this.API + path, formData, this.HTTP_OPTIONS));
  }

  /**
   * HTTP PATCH (file upload) wrapper.
   * @param path  path of API call.
   * @param body  stringified json body.
   */
  patchFileUrl(path: string, formData: any) {
    this.prepareHttpOptions(true);
    return this.loadingWrapper(this.http.patch(this.API + path, formData, this.HTTP_OPTIONS));
  }

  /**
   * HTTP DELETE wrapper.
   * @param path  path of API call.
   */
  deleteUrl(path: string) {
    this.prepareHttpOptions();
    return this.loadingWrapper(this.http.delete(this.API + path, this.HTTP_OPTIONS));
  }

  /**
   * Wrapper to display Loading-component during each network request.
   * @param path  path of API call.
   * @param body  stringified json body.
   */
  loadingWrapper(httpCall, isLoader = true) {
    const SELF = this;
    if (isLoader) {
      setTimeout(() => {this.globalService.toggleLoading(true); }, 100);
    }
    let success = (params) => {};
    let error = (params) => {};
    let final = () => {};
    const RETURN_WRAPPER = {
      subscribe: (fa, fb, fc) => {
        success = fa;
        error = fb;
        final = fc;
      }
    };
    httpCall.subscribe(
      (data) => {
        success(data);
      },
      (err) => {
        setTimeout(() => {this.globalService.toggleLoading(false); }, 100);
        error(err);
      },
      () => {
        setTimeout(() => {this.globalService.toggleLoading(false); } , 100);
        final();
      }
    );
    return RETURN_WRAPPER;
  }

  /**
   * Utility for appending extra headers
   */
  appendHeaders(headers) {
    // TODO: Add Headers to this.HEADERS and update this.HTTP_OPTIONS
  }
}
