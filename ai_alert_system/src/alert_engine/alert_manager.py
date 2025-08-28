"""
简化版智能告警引擎
专注于核心告警功能，支持邮件通知和控制台输出
"""
import logging
import asyncio
import smtplib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..models.data_models import Alert, AlertLevel
from ..config import settings

logger = logging.getLogger(__name__)

class SimpleAlertNotifier:
    """简化版告警通知器"""
    
    def __init__(self):
        self.email_config = {
            "smtp_host": settings.alert_email_smtp_host,
            "smtp_port": settings.alert_email_smtp_port,
            "user": settings.alert_email_user,
            "password": settings.alert_email_password
        }
        # 设置告警日志
        self.alert_logger = logging.getLogger('alerts')
        handler = logging.FileHandler('logs/alerts.log', encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.alert_logger.addHandler(handler)
        self.alert_logger.setLevel(logging.INFO)
    
    async def send_alert(self, alert: Alert):
        """发送告警通知"""
        # 控制台输出
        self._print_alert(alert)
        
        # 记录到告警日志
        self._log_alert(alert)
        
        # 邮件通知（仅对Critical和Emergency级别）
        if alert.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY] and self.email_config["user"]:
            try:
                await self._send_email(alert)
            except Exception as e:
                logger.error(f"邮件通知发送失败: {e}")
    
    def _print_alert(self, alert: Alert):
        """打印告警到控制台"""
        level_colors = {
            AlertLevel.INFO: "\033[36m",      # 青色
            AlertLevel.WARNING: "\033[33m",   # 黄色
            AlertLevel.CRITICAL: "\033[31m",  # 红色
            AlertLevel.EMERGENCY: "\033[91m"  # 亮红色
        }
        reset_color = "\033[0m"
        
        color = level_colors.get(alert.level, "")
        
        print(f"\n{color}[{alert.level.value.upper()}]{reset_color} {alert.title}")
        print(f"时间: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"主机: {alert.hostname}")
        print(f"当前值: {alert.current_value} (阈值: {alert.threshold_value})")
        
        if alert.suggested_actions:
            print("建议解决方案:")
            for i, action in enumerate(alert.suggested_actions[:3], 1):
                print(f"  {i}. {action}")
        print()
    
    def _log_alert(self, alert: Alert):
        """记录告警到日志文件"""
        log_message = (
            f"{alert.hostname} - {alert.title} - "
            f"当前值:{alert.current_value} 阈值:{alert.threshold_value}"
        )
        
        if alert.level == AlertLevel.CRITICAL:
            self.alert_logger.critical(log_message)
        elif alert.level == AlertLevel.WARNING:
            self.alert_logger.warning(log_message)
        elif alert.level == AlertLevel.EMERGENCY:
            self.alert_logger.critical(f"紧急告警: {log_message}")
        else:
            self.alert_logger.info(log_message)
    
    async def _send_email(self, alert: Alert):
        """发送邮件通知"""
        try:
            # 创建邮件内容
            msg = MIMEMultipart()
            msg["From"] = self.email_config["user"]
            msg["To"] = self.email_config["user"]  # 简化：发给自己
            msg["Subject"] = f"[{alert.level.value.upper()}] {alert.title}"
            
            # 邮件正文
            body = self._create_email_body(alert)
            msg.attach(MIMEText(body, "html", "utf-8"))
            
            # 发送邮件
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_smtp_email, msg
            )
            
            print(f"📧 [邮件已发送] {alert.title}")
            logger.info(f"邮件通知已发送: {alert.id}")
        
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            raise
    
    def _send_smtp_email(self, msg: MIMEMultipart):
        """发送SMTP邮件（同步操作）"""
        with smtplib.SMTP(self.email_config["smtp_host"], self.email_config["smtp_port"]) as server:
            server.starttls()
            server.login(self.email_config["user"], self.email_config["password"])
            server.send_message(msg)
    
    def _create_email_body(self, alert: Alert) -> str:
        """创建邮件正文"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: {'#d32f2f' if alert.level == AlertLevel.CRITICAL else '#f57c00'};">
                系统监控告警
            </h2>
            <table border="1" style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px;"><strong>告警级别</strong></td>
                    <td style="padding: 10px; color: {'#d32f2f' if alert.level == AlertLevel.CRITICAL else '#f57c00'};">
                        {alert.level.value.upper()}
                    </td>
                </tr>
                <tr><td style="padding: 10px;"><strong>主机名</strong></td><td style="padding: 10px;">{alert.hostname}</td></tr>
                <tr><td style="padding: 10px;"><strong>时间</strong></td><td style="padding: 10px;">{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                <tr><td style="padding: 10px;"><strong>告警内容</strong></td><td style="padding: 10px;">{alert.description}</td></tr>
                <tr><td style="padding: 10px;"><strong>当前值</strong></td><td style="padding: 10px;">{alert.current_value}</td></tr>
                <tr><td style="padding: 10px;"><strong>阈值</strong></td><td style="padding: 10px;">{alert.threshold_value}</td></tr>
            </table>
            
            <h3 style="color: #1976d2;">AI推荐的解决方案：</h3>
            <ul style="margin: 10px 0; padding-left: 20px;">
                {''.join([f'<li style="margin: 5px 0;">{action}</li>' for action in alert.suggested_actions])}
            </ul>
            
            <hr style="margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">
                此告警由AI智能告警系统自动生成<br>
                系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </body>
        </html>
        """

class AlertManager:
    """简化版告警管理器"""
    
    def __init__(self):
        self.notifier = SimpleAlertNotifier()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.suppression_rules: Dict[str, datetime] = {}
    
    async def process_alert(self, alert: Alert):
        """处理告警"""
        # 检查告警抑制
        if self._is_suppressed(alert):
            logger.debug(f"告警 {alert.id} 被抑制")
            return
        
        # 去重处理
        existing_alert = self._find_similar_alert(alert)
        if existing_alert:
            await self._update_existing_alert(existing_alert, alert)
        else:
            await self._create_new_alert(alert)
    
    def _is_suppressed(self, alert: Alert) -> bool:
        """检查告警是否被抑制"""
        suppression_key = f"{alert.hostname}_{alert.metric_type.value}"
        
        if suppression_key in self.suppression_rules:
            suppression_end = self.suppression_rules[suppression_key]
            if datetime.now() < suppression_end:
                return True
            else:
                # 抑制期已过，移除规则
                del self.suppression_rules[suppression_key]
        
        return False
    
    def _find_similar_alert(self, alert: Alert) -> Optional[Alert]:
        """查找相似的活跃告警"""
        for existing_alert in self.active_alerts.values():
            if (existing_alert.hostname == alert.hostname and
                existing_alert.metric_type == alert.metric_type and
                not existing_alert.resolved):
                return existing_alert
        return None
    
    async def _update_existing_alert(self, existing_alert: Alert, new_alert: Alert):
        """更新现有告警"""
        # 更新值和时间
        existing_alert.current_value = new_alert.current_value
        existing_alert.timestamp = new_alert.timestamp
        
        # 如果级别升级，发送通知
        if new_alert.level.value != existing_alert.level.value:
            existing_alert.level = new_alert.level
            existing_alert.description = new_alert.description
            print(f"⬆️ 告警级别升级: {existing_alert.title}")
            await self.notifier.send_alert(existing_alert)
            logger.info(f"告警 {existing_alert.id} 级别升级为 {new_alert.level.value}")
    
    async def _create_new_alert(self, alert: Alert):
        """创建新告警"""
        # 添加到活跃告警
        self.active_alerts[alert.id] = alert
        
        # 添加到历史记录
        self.alert_history.append(alert)
        
        # 发送通知
        await self.notifier.send_alert(alert)
        
        logger.info(f"创建新告警 {alert.id} - {alert.hostname}")
    
    def resolve_alert(self, alert_id: str):
        """解决告警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            del self.active_alerts[alert_id]
            print(f"✅ 告警已解决: {alert.title}")
            logger.info(f"告警已解决: {alert_id}")
    
    def suppress_alerts(self, hostname: str, metric_type: str, duration_minutes: int):
        """抑制告警"""
        suppression_key = f"{hostname}_{metric_type}"
        suppression_end = datetime.now() + timedelta(minutes=duration_minutes)
        self.suppression_rules[suppression_key] = suppression_end
        print(f"🔇 告警抑制: {suppression_key} ({duration_minutes}分钟)")
        logger.info(f"告警抑制: {suppression_key} 直到 {suppression_end}")
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return list(self.active_alerts.values())
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计信息"""
        total_alerts = len(self.alert_history)
        active_count = len(self.active_alerts)
        
        # 按级别统计
        level_stats = {}
        for level in AlertLevel:
            level_stats[level.value] = sum(
                1 for alert in self.alert_history 
                if alert.level == level
            )
        
        # 按主机统计
        hostname_stats = {}
        for alert in self.alert_history:
            hostname_stats[alert.hostname] = hostname_stats.get(alert.hostname, 0) + 1
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_count,
            "resolved_alerts": total_alerts - active_count,
            "level_distribution": level_stats,
            "hostname_distribution": hostname_stats
        }
