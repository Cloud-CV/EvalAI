import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';

// import component
import { PrivacyPolicyComponent } from './privacy-policy.component';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { FooterComponent } from '../../components/nav/footer/footer.component';

// import service
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';
import { EndpointsService } from '../../services/endpoints.service';

describe('PrivacyPolicyComponent', () => {
  let component: PrivacyPolicyComponent;
  let fixture: ComponentFixture<PrivacyPolicyComponent>;
  let de: DebugElement;
  let ALL_NAV;
  let ALL_TARGET;

  const fakeActivatedRoute = {
    snapshot: { data: {} },
  } as ActivatedRoute;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [PrivacyPolicyComponent, HeaderStaticComponent, FooterComponent],
      providers: [GlobalService, AuthService, ApiService, EndpointsService],
      imports: [HttpClientModule, RouterTestingModule],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PrivacyPolicyComponent);
    component = fixture.componentInstance;
    de = fixture.debugElement;
    fixture.detectChanges();
    ALL_NAV = de.queryAll(By.css('.privacy-nav'));
    ALL_TARGET = de.queryAll(By.css('.privacy-section-title'));
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have only one scroll-selected element after page loads', () => {
    const scrollSelected = de.queryAll(By.css('.scroll-selected'));
    expect(scrollSelected.length).toBe(1);
  });

  it('should have the first title of the privacy nav of scroll-selected element', () => {
    const scrollSelected = de.query(By.css('.scroll-selected'));
    const expectedPrivacyNavTitle = 'What personal information do we collect ?';
    expect(scrollSelected.nativeElement.innerText).toBe(expectedPrivacyNavTitle);
  });

  it('should have equal number of section-title elements as nav elements', () => {
    expect(ALL_NAV.length).toBeGreaterThan(0);
    expect(ALL_TARGET.length).toBeGreaterThan(0);
    expect(ALL_TARGET.length).toBe(ALL_NAV.length);
  });

  it('should have same section title as nav element title', () => {
    ALL_NAV.forEach((ele, index) => {
      expect(ALL_TARGET[index].nativeElement.innerText).toBe(ele.nativeElement.innerText);
    });
  });

  it('should have called the scroll function when scroll selected element is called', () => {
    const scrollSelected = de.query(By.css('.scroll-selected'));
    scrollSelected.nativeElement.click();

    fixture.whenStable().then(() => {
      expect(component.scroll).toHaveBeenCalled();
      expect(component.highlightNav).toHaveBeenCalled();
      expect(component.highlightSectionTitle).toHaveBeenCalled();
    });
  });
});
