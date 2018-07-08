import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { GlobalService } from '../global.service';

const HEADERS = { 'Content-Type': 'application/json' };

@Injectable()
export class ApiService {
  API = environment.api_endpoint;
  constructor(private http: HttpClient, private globalService: GlobalService) { }

  getUrl(path: string) {
    return this.http.get(this.API + path);
  }

  postUrl(path: string, body: string) {
    const TOKEN = this.globalService.getAuthToken();
    if (TOKEN) {
      HEADERS['Authorization'] = 'Token ' + TOKEN;
    }
    const HTTP_OPTIONS = {
      headers: new HttpHeaders(HEADERS)
    };
    return this.http.post(this.API + path, body, HTTP_OPTIONS);
  }
}
